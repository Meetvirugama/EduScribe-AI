"""
services/content/markdown_builder.py — Phase 1: Unified Markdown Generator

Merges the transcript segments and vision frames (OCR) into a single, 
structured Markdown document with chunk metadata. This becomes the single
source of truth that all Phase 2 extraction services read from.

Architecture rule (per pipeline design):
    Transcript + Vision → unified_md → [definitions, concepts, formulas,
    keywords, relations, examples, topics] → detailed_notes_md → artifacts
"""
from typing import Any, Dict, List
import logging

logger = logging.getLogger(__name__)


def _fmt_time(sec: float) -> str:
    """Convert seconds to HH:MM:SS."""
    m, s = divmod(int(sec), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def build_unified_markdown(
    segments: List[Dict[str, Any]],
    frames: List[Dict[str, Any]],
    metadata: Dict[str, Any],
    chunk_duration_sec: float = 180.0,
) -> str:
    """
    Merge transcript segments and vision frames into a single Markdown document
    structured in temporal chunks. Each chunk contains the transcript text and
    any OCR text from frames that fall within its time window.

    Args:
        segments:  Raw transcript segments [{text, start, end|duration}, ...]
        frames:    Merged frames [{path, time_sec, ocr, scene_number}, ...]
        metadata:  Video metadata dict (video_id, title, etc.)
        chunk_duration_sec: Target chunk length in seconds (default: 3 min)

    Returns:
        A string — structured GitHub Flavored Markdown document.
    """
    if not segments:
        logger.warning("build_unified_markdown: no transcript segments provided.")
        return "# Lecture Content\n\n*No transcript available.*\n"

    video_id = metadata.get("video_id", "unknown")
    title = metadata.get("title", "Untitled Lecture")

    lines: List[str] = [
        f"# {title}",
        f"",
        f"> **Video ID:** `{video_id}`",
        f"",
    ]

    # ── Build time-bounded chunks ──────────────────────────────────────────────
    chunks: List[Dict[str, Any]] = []
    current_segs: List[str] = []
    current_start: float = None
    current_end: float = 0.0
    chunk_idx = 0

    for seg in segments:
        seg_start = float(seg.get("start", 0.0))
        seg_text = seg.get("text", "").strip()
        if not seg_text:
            continue

        if current_start is None:
            current_start = seg_start

        current_segs.append(seg_text)

        if "end" in seg:
            current_end = float(seg["end"])
        elif "duration" in seg:
            current_end = seg_start + float(seg.get("duration", 0.0))
        else:
            current_end = seg_start

        if (current_end - current_start) >= chunk_duration_sec or \
                sum(len(t) for t in current_segs) > 2000:
            chunks.append({
                "chunk_id": f"{video_id}_chunk_{chunk_idx}",
                "start": current_start,
                "end": current_end,
                "text": " ".join(current_segs),
            })
            chunk_idx += 1
            current_segs = []
            current_start = None

    # Flush last chunk
    if current_segs:
        chunks.append({
            "chunk_id": f"{video_id}_chunk_{chunk_idx}",
            "start": current_start if current_start is not None else 0.0,
            "end": current_end,
            "text": " ".join(current_segs),
        })

    # ── Build frame lookup by time_sec ────────────────────────────────────────
    # frames is a list of dicts with keys: path, time_sec, ocr, scene_number
    sorted_frames = sorted(frames, key=lambda f: f.get("time_sec", 0.0))

    # ── Render each chunk to Markdown ─────────────────────────────────────────
    for c in chunks:
        c_start = c["start"]
        c_end = c["end"]
        c_id = c["chunk_id"]

        lines.append(
            f"## Chunk `{c_id}` — {_fmt_time(c_start)} to {_fmt_time(c_end)}"
        )
        lines.append("")

        # Transcript text
        lines.append("### Transcript")
        lines.append("")
        lines.append(c["text"])
        lines.append("")

        # OCR frames that fall inside this chunk's time window
        chunk_frames = [
            f for f in sorted_frames
            if c_start <= f.get("time_sec", 0.0) <= c_end
            and f.get("ocr", "").strip()
        ]

        if chunk_frames:
            lines.append("### Visual Content (OCR from Slides/Frames)")
            lines.append("")
            for frm in chunk_frames:
                ts = _fmt_time(frm["time_sec"])
                scene = frm.get("scene_number", "?")
                ocr = frm.get("ocr", "").strip()
                lines.append(f"**[{ts} | Scene {scene}]**")
                lines.append("")
                lines.append(f"> {ocr}")
                lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)
