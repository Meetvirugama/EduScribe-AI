"""
services/merge/models.py — MergedLecture structured data models.

These are the source-of-truth data structures that the entire downstream
Content Pipeline and Artifact Generators read from.

Architecture rule (from spec):
    merged_lecture.json  ← SOURCE OF TRUTH (structured, machine-readable)
    merged_lecture.md    ← human-readable derivative for inspection/debugging

Do NOT build downstream logic on Markdown parsing.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class MergedFrame:
    """
    A single selected keyframe with its associated visual intelligence.

    frame_path: web-relative path (e.g. storage/frames/{video_id}/scene_0001.jpg)
    timestamp_sec: position in the video in seconds
    ocr_text: cleaned OCR text extracted from the frame (may be empty/None)
    importance_score: visual_importance_score from FrameScore (0.0–1.0)
    scene_number: which scene this frame belongs to
    transcript_similarity: how closely OCR matches nearby transcript text
    """
    frame_path: str
    timestamp_sec: float
    scene_number: int
    ocr_text: Optional[str] = None
    importance_score: float = 0.0
    transcript_similarity: float = 0.0


@dataclass
class MergedSection:
    """
    A temporal section of the lecture where transcript and visual data are aligned.

    Each section corresponds to one logical content block — typically bounded by
    scene changes and/or topic boundaries from the transcript.
    """
    section_id: str
    start_time: float          # seconds
    end_time: float            # seconds
    transcript_segments: List[Dict[str, Any]] = field(default_factory=list)
    frames: List[MergedFrame] = field(default_factory=list)
    scene_numbers: List[int] = field(default_factory=list)

    @property
    def full_text(self) -> str:
        """Concatenated transcript text for this section."""
        return " ".join(s.get("text", "").strip()
                        for s in self.transcript_segments if s.get("text"))



    @property
    def duration_seconds(self) -> float:
        return max(0.0, self.end_time - self.start_time)


@dataclass
class MergedLecture:
    """
    The canonical, unified representation of a processed lecture.

    Produced by MergeBuilder after Vision Pipeline + Transcription complete.
    Used by ContentPipeline as its sole input source.

    Fields:
        video_id:   string UUID of the video
        metadata:   title, duration, channel, etc.
        sections:   chronological list of aligned transcript+visual sections
        statistics: pipeline stats (frame count, OCR rate, etc.)
    """
    video_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    sections: List[MergedSection] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_duration(self) -> float:
        """Total lecture duration in seconds."""
        if not self.sections:
            return 0.0
        return self.sections[-1].end_time

    @property
    def all_transcript_segments(self) -> List[Dict[str, Any]]:
        """Flat list of all transcript segments across sections."""
        segments = []
        for sec in self.sections:
            segments.extend(sec.transcript_segments)
        return segments

    @property
    def all_frames(self) -> List[MergedFrame]:
        """Flat list of all selected frames across sections."""
        frames = []
        for sec in self.sections:
            frames.extend(sec.frames)
        return frames

    @property
    def full_transcript_text(self) -> str:
        """Full concatenated transcript for the entire lecture."""
        return " ".join(
            s.get("text", "").strip()
            for sec in self.sections
            for s in sec.transcript_segments
            if s.get("text")
        )
