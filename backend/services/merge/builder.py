"""
services/merge/builder.py — MergeBuilder

Builds the MergedLecture structured object by aligning:
  - Transcript segments (from Whisper JSON)
  - Selected keyframes + OCR (from Vision Pipeline / DB)
  - Scene information

Writes two output files:
  1. merged_lecture.json   ← SOURCE OF TRUTH (machine-readable)
  2. merged_lecture.md     ← human-readable representation for debugging

Architecture rule:
  Downstream Content Pipeline and all Artifact Generators must read from
  merged_lecture.json only. They must NOT read raw video or transcript files.
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from typing import Any, Dict, List, Optional

from core.config import settings
from services.merge.models import MergedFrame, MergedLecture, MergedSection

logger = logging.getLogger(__name__)

# Gap (seconds) within which a frame is considered part of the same section
# as a group of transcript segments
FRAME_SECTION_TOLERANCE_SEC = 30.0


class MergeBuilder:
    """
    Aligns transcript segments and selected frames into a MergedLecture.

    Algorithm:
      1. Sort transcript segments by start time.
      2. Detect section boundaries using scene changes and natural pauses.
      3. For each section, collect transcript segments that fall within it.
      4. Assign frames to sections by timestamp proximity.
      5. Emit MergedLecture with ordered MergedSection list.
    """

    def build(
        self,
        video_id: str,
        transcript_segments: List[Dict[str, Any]],
        frames_data: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MergedLecture:
        """
        Build and return a MergedLecture object.

        Args:
            video_id: String UUID of the video.
            transcript_segments: Whisper segment list [{text, start, end}, ...].
            frames_data: Selected frames [{path, time_sec, ocr, scene_number,
                          visual_importance_score, transcript_similarity}, ...].
            metadata: Optional video metadata dict.

        Returns:
            MergedLecture — the unified aligned representation.
        """
        logger.info("MergeBuilder.build() starting for video %s", video_id)

        # ── 1. Normalise and sort inputs ─────────────────────────────────────
        segments = sorted(
            [s for s in transcript_segments if s.get("text", "").strip()],
            key=lambda s: float(s.get("start", 0)),
        )
        frames = sorted(frames_data, key=lambda f: float(f.get("time_sec", 0)))

        if not segments:
            logger.warning("MergeBuilder: no transcript segments for video %s", video_id)

        # ── 2. Build sections from scene boundaries ──────────────────────────
        sections = self._build_sections(segments, frames, video_id)

        # ── 3. Compute statistics ────────────────────────────────────────────
        total_ocr = sum(
            1 for sec in sections for f in sec.frames if f.ocr_text and f.ocr_text.strip()
        )
        stats = {
            "section_count": len(sections),
            "total_frames": sum(len(s.frames) for s in sections),
            "total_segments": len(segments),
            "frames_with_ocr": total_ocr,
            "total_duration_sec": sections[-1].end_time if sections else 0,
        }

        lecture = MergedLecture(
            video_id=video_id,
            metadata=metadata or {},
            sections=sections,
            statistics=stats,
        )

        logger.info(
            "MergeBuilder: built %d sections, %d frames, %d segments for video %s",
            len(sections), sum(len(s.frames) for s in sections), len(segments), video_id,
        )
        return lecture

    # ── Private helpers ──────────────────────────────────────────────────────

    def _build_sections(
        self,
        segments: List[Dict[str, Any]],
        frames: List[Dict[str, Any]],
        video_id: str,
    ) -> List[MergedSection]:
        """
        Group transcript segments and frames into temporal sections.

        Section boundaries are determined by:
          - Scene changes (different scene_number in adjacent frames)
          - Long pauses (gap > FRAME_SECTION_TOLERANCE_SEC between segments)
        """
        if not segments and not frames:
            return []

        # Collect all unique scene numbers and build scene time boundaries
        scene_boundaries = self._extract_scene_boundaries(frames)

        if not scene_boundaries:
            # No frame data — create one section per significant transcript pause
            return self._sections_from_transcript(segments, video_id)

        sections: List[MergedSection] = []

        for i, (scene_start, scene_end, scene_num) in enumerate(scene_boundaries):
            section_id = f"{video_id}_sec_{i:04d}"

            # Gather transcript segments that overlap with this scene window
            scene_segs = [
                s for s in segments
                if _overlaps(
                    float(s.get("start", 0)),
                    float(s.get("end", s.get("start", 0))),
                    scene_start,
                    scene_end,
                )
            ]

            # Gather frames belonging to this scene
            scene_frames = [
                MergedFrame(
                    frame_path=f.get("path", ""),
                    timestamp_sec=float(f.get("time_sec", 0)),
                    scene_number=int(f.get("scene_number", scene_num)),
                    ocr_text=f.get("ocr") or None,
                    importance_score=float(f.get("visual_importance_score", 0.0)),
                    transcript_similarity=float(f.get("transcript_similarity", 0.0)),
                )
                for f in frames
                if int(f.get("scene_number", -1)) == scene_num
            ]

            section = MergedSection(
                section_id=section_id,
                start_time=scene_start,
                end_time=scene_end,
                transcript_segments=scene_segs,
                frames=scene_frames,
                scene_numbers=[scene_num],
            )
            sections.append(section)

        # Handle any transcript segments that didn't map to any scene
        mapped_seg_starts = {
            s.get("start")
            for sec in sections
            for s in sec.transcript_segments
        }
        orphan_segs = [s for s in segments if s.get("start") not in mapped_seg_starts]
        if orphan_segs:
            orphan_section = MergedSection(
                section_id=f"{video_id}_sec_orphan",
                start_time=float(orphan_segs[0].get("start", 0)),
                end_time=float(orphan_segs[-1].get("end", orphan_segs[-1].get("start", 0))),
                transcript_segments=orphan_segs,
                frames=[],
                scene_numbers=[],
            )
            sections.append(orphan_section)
            sections.sort(key=lambda s: s.start_time)

        return sections

    def _extract_scene_boundaries(
        self, frames: List[Dict[str, Any]]
    ) -> List[tuple]:
        """
        Returns list of (start_sec, end_sec, scene_number) tuples.

        Builds scene boundaries from frame metadata by grouping consecutive
        frames with the same scene_number.
        """
        if not frames:
            return []

        # Group frames by scene_number, track min/max timestamp per scene
        scene_times: Dict[int, List[float]] = {}
        for f in frames:
            sn = int(f.get("scene_number", 0))
            ts = float(f.get("time_sec", 0))
            scene_times.setdefault(sn, []).append(ts)

        boundaries = []
        scene_nums = sorted(scene_times.keys())
        for i, sn in enumerate(scene_nums):
            times = scene_times[sn]
            scene_start = min(times)
            # Scene end = start of next scene or max time of current scene + small buffer
            if i + 1 < len(scene_nums):
                next_sn = scene_nums[i + 1]
                scene_end = min(scene_times[next_sn])
            else:
                scene_end = max(times) + FRAME_SECTION_TOLERANCE_SEC
            boundaries.append((scene_start, scene_end, sn))

        return boundaries

    def _sections_from_transcript(
        self, segments: List[Dict[str, Any]], video_id: str
    ) -> List[MergedSection]:
        """
        Fallback: when no frames are available, create sections by grouping
        transcript segments using pause-based boundaries.
        """
        if not segments:
            return []

        PAUSE_THRESHOLD = 10.0  # seconds gap between segments = new section
        sections: List[MergedSection] = []
        current_group: List[Dict] = [segments[0]]

        for seg in segments[1:]:
            prev_end = float(current_group[-1].get("end", current_group[-1].get("start", 0)))
            curr_start = float(seg.get("start", 0))
            if curr_start - prev_end > PAUSE_THRESHOLD:
                sections.append(self._group_to_section(current_group, video_id, len(sections)))
                current_group = [seg]
            else:
                current_group.append(seg)

        if current_group:
            sections.append(self._group_to_section(current_group, video_id, len(sections)))

        return sections

    def _group_to_section(
        self, group: List[Dict], video_id: str, idx: int
    ) -> MergedSection:
        return MergedSection(
            section_id=f"{video_id}_sec_{idx:04d}",
            start_time=float(group[0].get("start", 0)),
            end_time=float(group[-1].get("end", group[-1].get("start", 0))),
            transcript_segments=group,
            frames=[],
            scene_numbers=[],
        )


def _overlaps(seg_start: float, seg_end: float, win_start: float, win_end: float) -> bool:
    """True if [seg_start, seg_end] overlaps with [win_start, win_end]."""
    return seg_start <= win_end and seg_end >= win_start


# ── Serialise / Deserialise ───────────────────────────────────────────────────

def merged_lecture_to_dict(lecture: MergedLecture) -> Dict[str, Any]:
    """Serialize MergedLecture to a JSON-safe dict."""
    return {
        "video_id": lecture.video_id,
        "metadata": lecture.metadata,
        "statistics": lecture.statistics,
        "sections": [
            {
                "section_id": sec.section_id,
                "start_time": sec.start_time,
                "end_time": sec.end_time,
                "scene_numbers": sec.scene_numbers,
                "transcript_segments": sec.transcript_segments,
                "frames": [
                    {
                        "frame_path": f.frame_path,
                        "timestamp_sec": f.timestamp_sec,
                        "scene_number": f.scene_number,
                        "ocr_text": f.ocr_text,
                        "importance_score": f.importance_score,
                        "transcript_similarity": f.transcript_similarity,
                    }
                    for f in sec.frames
                ],
            }
            for sec in lecture.sections
        ],
    }


def merged_lecture_from_dict(data: Dict[str, Any]) -> MergedLecture:
    """Deserialize a MergedLecture from a JSON-loaded dict."""
    sections = []
    for s in data.get("sections", []):
        frames = [
            MergedFrame(
                frame_path=f["frame_path"],
                timestamp_sec=f["timestamp_sec"],
                scene_number=f["scene_number"],
                ocr_text=f.get("ocr_text"),
                importance_score=f.get("importance_score", 0.0),
                transcript_similarity=f.get("transcript_similarity", 0.0),
            )
            for f in s.get("frames", [])
        ]
        sections.append(
            MergedSection(
                section_id=s["section_id"],
                start_time=s["start_time"],
                end_time=s["end_time"],
                transcript_segments=s.get("transcript_segments", []),
                frames=frames,
                scene_numbers=s.get("scene_numbers", []),
            )
        )
    return MergedLecture(
        video_id=data["video_id"],
        metadata=data.get("metadata", {}),
        sections=sections,
        statistics=data.get("statistics", {}),
    )


def save_merged_lecture(lecture: MergedLecture, output_dir: str) -> str:
    """
    Write merged_lecture.json to disk.

    Returns: absolute path to the written file.
    """
    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, "merged_lecture.json")
    data = merged_lecture_to_dict(lecture)
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    logger.info("MergedLecture saved to %s (%d bytes)", json_path, os.path.getsize(json_path))
    return json_path


def load_merged_lecture(json_path: str) -> MergedLecture:
    """Load MergedLecture from a merged_lecture.json path."""
    with open(json_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return merged_lecture_from_dict(data)


def render_merged_lecture_md(lecture: MergedLecture, output_dir: str) -> str:
    """
    Write a human-readable merged_lecture.md for inspection/debugging.

    This is NOT the source of truth — it is a derivative rendering only.
    Returns: absolute path to the written file.
    """
    os.makedirs(output_dir, exist_ok=True)
    md_path = os.path.join(output_dir, "merged_lecture.md")

    lines = [
        f"# Merged Lecture — {lecture.metadata.get('title', lecture.video_id)}\n",
        f"> Generated by EduScribe AI — source of truth is `merged_lecture.json`\n",
        f"---\n",
        f"**Video ID:** `{lecture.video_id}`  \n",
        f"**Duration:** {lecture.total_duration:.1f}s  \n",
        f"**Sections:** {len(lecture.sections)}  \n",
        f"**Total Frames:** {lecture.statistics.get('total_frames', 0)}  \n",
        "\n---\n",
    ]

    for sec in lecture.sections:
        start_fmt = _fmt_time(sec.start_time)
        end_fmt = _fmt_time(sec.end_time)
        lines.append(f"\n## Section `{sec.section_id}` [{start_fmt} → {end_fmt}]\n")

        if sec.transcript_segments:
            lines.append("**Transcript:**\n")
            for seg in sec.transcript_segments:
                ts = _fmt_time(float(seg.get("start", 0)))
                text = seg.get("text", "").strip()
                lines.append(f"> [{ts}] {text}")
            lines.append("")

        if sec.frames:
            lines.append("**Visual Frames:**\n")
            for f in sec.frames:
                ts = _fmt_time(f.timestamp_sec)
                ocr_preview = (f.ocr_text or "")[:100].replace("\n", " ")
                lines.append(
                    f"- `{ts}` Scene {f.scene_number} | "
                    f"importance={f.importance_score:.2f} | "
                    f"OCR: {ocr_preview or '—'}"
                )
            lines.append("")

        lines.append("---\n")

    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    logger.info("Merged lecture markdown written to %s", md_path)
    return md_path


def _fmt_time(seconds: float) -> str:
    """Format seconds as HH:MM:SS."""
    try:
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"
    except Exception:
        return "00:00:00"


# Module-level singleton
merge_builder = MergeBuilder()
