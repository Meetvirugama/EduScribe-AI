"""
Transcript matching service using RapidFuzz for fast, dependency-light similarity.

Computes the similarity between a frame's OCR text and the closest
Whisper transcript chunk based on the frame's timestamp.
"""
import json
import logging
import os
from typing import List, Dict, Any, Optional

from rapidfuzz import fuzz

from core.config import settings

logger = logging.getLogger(__name__)

# Minimum similarity score (0–100) to consider a match relevant
MIN_SIMILARITY: float = getattr(settings, "TRANSCRIPT_MATCH_MIN_SCORE", 10.0)


class TranscriptMatcherService:
    """
    Matches video frames to Whisper transcript segments by timestamp,
    then scores semantic overlap between OCR text and the spoken words.

    Design choice – RapidFuzz over SentenceTransformers:
        SentenceTransformers requires ~400 MB of model weights and significant
        RAM. RapidFuzz is a pure-Python C extension with zero model weight
        overhead. For slide OCR vs. transcript matching, token set ratio
        (which ignores word order) reliably captures keyword overlap between
        a slide's bullet points and the spoken explanation.
        SentenceTransformers can be added as an optional upgrade in Phase 2
        without changing this interface.
    """

    def find_matching_segment(
        self,
        timestamp_ms: int,
        transcript_segments: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """
        Find the transcript segment whose time window contains the given timestamp.

        Falls back to the nearest segment by midpoint distance if no exact match.

        Args:
            timestamp_ms:        Frame timestamp in milliseconds.
            transcript_segments: List of segment dicts with 'start', 'end', 'text' keys.

        Returns:
            The best matching segment dict, or None if the list is empty.
        """
        if not transcript_segments:
            return None

        timestamp_s = timestamp_ms / 1000.0

        # 1. Exact range match
        for seg in transcript_segments:
            if seg.get("start", 0) <= timestamp_s <= seg.get("end", 0):
                return seg

        # 2. Nearest midpoint fallback
        def midpoint_distance(seg: Dict[str, Any]) -> float:
            mid = (seg.get("start", 0) + seg.get("end", 0)) / 2.0
            return abs(mid - timestamp_s)

        return min(transcript_segments, key=midpoint_distance)

    def score_similarity(self, ocr_text: str, transcript_text: str) -> float:
        """
        Score the textual similarity between OCR output and a transcript segment.

        Uses RapidFuzz token_set_ratio which normalises for word order differences
        and subset relationships (e.g., a slide heading matching part of a sentence).

        Args:
            ocr_text:        Cleaned OCR text from the frame.
            transcript_text: Text from the matching transcript segment.

        Returns:
            Similarity score in the range [0.0, 1.0].
        """
        if not ocr_text or not transcript_text:
            return 0.0

        raw_score = fuzz.token_set_ratio(
            ocr_text.lower(), transcript_text.lower()
        )
        return round(raw_score / 100.0, 4)

    def match_frames_to_transcript(
        self,
        frames: List[Dict[str, Any]],
        transcript_path: str,
    ) -> List[Dict[str, Any]]:
        """
        Add transcript similarity scores to a list of frame dicts.

        Loads the transcript JSON once, then matches each frame by timestamp
        and scores its OCR text against the matching segment.

        Args:
            frames:          List of frame dicts (must include 'timestamp_ms' and 'clean_text').
            transcript_path: Absolute path to the Whisper transcript JSON file.

        Returns:
            The input list with each dict augmented by:
                - 'transcript_text' (str): The matched spoken text.
                - 'transcript_similarity' (float): Similarity score [0, 1].
        """
        if not os.path.exists(transcript_path):
            logger.warning("Transcript file not found: %s – using 0 similarity.", transcript_path)
            return [{**f, "transcript_text": "", "transcript_similarity": 0.0} for f in frames]

        try:
            with open(transcript_path, "r", encoding="utf-8") as fh:
                transcript_segments: List[Dict[str, Any]] = json.load(fh)
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Failed to load transcript from %s: %s", transcript_path, exc)
            return [{**f, "transcript_text": "", "transcript_similarity": 0.0} for f in frames]

        enriched: List[Dict[str, Any]] = []
        for frame in frames:
            ts_ms = frame.get("timestamp_ms", 0)
            ocr_text = frame.get("clean_text", "") or ""

            segment = self.find_matching_segment(ts_ms, transcript_segments)
            seg_text = segment.get("text", "") if segment else ""

            similarity = self.score_similarity(ocr_text, seg_text)
            enriched.append(
                {
                    **frame,
                    "transcript_text": seg_text,
                    "transcript_similarity": similarity,
                }
            )

        logger.debug("Matched %d frames to transcript segments.", len(enriched))
        return enriched


transcript_matcher_service = TranscriptMatcherService()
