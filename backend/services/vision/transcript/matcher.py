"""
Transcript matching service using RapidFuzz for fast, dependency-light similarity.
Optimized with O(log N) indexing, text normalization, and caching.
"""
import json
import logging
import os
from typing import List, Dict, Any

from rapidfuzz import fuzz
from core.config import settings

from services.vision.transcript.index import TranscriptIndex
from services.vision.transcript.normalizer import normalize_text
from services.vision.transcript.cache import transcript_cache

logger = logging.getLogger(__name__)

# Minimum similarity score (0–100) to consider a match relevant
MIN_SIMILARITY: float = getattr(settings, "TRANSCRIPT_MATCH_MIN_SCORE", 10.0)
TRANSCRIPT_CONTEXT_WINDOW: int = getattr(settings, "TRANSCRIPT_CONTEXT_WINDOW", 1)


class TranscriptMatcherService:
    """
    Matches video frames to Whisper transcript segments by timestamp.
    
    RapidFuzz is used instead of embedding models because slide OCR
    and transcript matching mainly depend on keyword overlap.
    This avoids loading large neural models and keeps memory usage low.
    """

    def _get_or_create_index(self, transcript_path: str, video_id: str) -> TranscriptIndex:
        cached = transcript_cache.get_index(video_id)
        if cached:
            return cached

        try:
            with open(transcript_path, "r", encoding="utf-8") as fh:
                segments: List[Dict[str, Any]] = json.load(fh)
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Failed to load transcript from %s: %s", transcript_path, exc)
            segments = []

        index = TranscriptIndex(segments)
        transcript_cache.set_index(video_id, index)
        return index

    def score_similarity(self, ocr_text: str, transcript_text: str) -> float:
        """
        Score the textual similarity between OCR output and a transcript segment.
        """
        norm_ocr = normalize_text(ocr_text)
        norm_trans = normalize_text(transcript_text)
        
        if not norm_ocr or not norm_trans:
            return 0.0

        # Token set ratio handles subsets (slide bullets inside spoken paragraphs)
        raw_score = fuzz.token_set_ratio(norm_ocr, norm_trans)
        return round(raw_score / 100.0, 4)

    def match_frames_to_transcript(
        self,
        frames: List[Dict[str, Any]],
        transcript_path: str,
        video_id: str
    ) -> List[Dict[str, Any]]:
        """
        Transcript matching is executed after pHash filtering because
        duplicate frames should not consume additional processing time.
        """
        if not os.path.exists(transcript_path):
            logger.warning("Transcript file not found: %s – using 0 similarity.", transcript_path)
            return [{
                **f,
                "transcript_text": "",
                "transcript_similarity": 0.0,
                "matched_segment_id": None,
                "matching_method": "none"
            } for f in frames]

        index = self._get_or_create_index(transcript_path, video_id)
        enriched: List[Dict[str, Any]] = []

        for frame in frames:
            ts_ms = frame.get("timestamp_ms", 0)
            ocr_text = frame.get("clean_text", "")

            candidates = index.get_context_segments(ts_ms, window=TRANSCRIPT_CONTEXT_WINDOW)
            
            best_score = 0.0
            best_seg = None
            
            for seg in candidates:
                score = self.score_similarity(ocr_text, seg.get("text", ""))
                if score > best_score:
                    best_score = score
                    best_seg = seg

            enriched.append({
                **frame,
                "transcript_text": best_seg.get("text", "") if best_seg else "",
                "transcript_similarity": best_score,
                "matched_segment_id": best_seg.get("id", None) if best_seg else None,
                "matching_method": "rapidfuzz_token_set_ratio" if best_seg else "none"
            })

        logger.debug("Matched %d frames to transcript segments using O(log N) index.", len(enriched))
        return enriched

transcript_matcher_service = TranscriptMatcherService()
