"""
Visual importance scoring engine for extracted video frames.

Produces a composite score (0–1) that drives final frame selection,
combining sharpness, OCR richness, transcript relevance, and scene duration.
"""
import logging
import re
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Scoring weights – must sum to 1.0
# ---------------------------------------------------------------------------
WEIGHT_TRANSCRIPT_SIMILARITY: float = 0.30
WEIGHT_OCR_RICHNESS:          float = 0.30
WEIGHT_EDUCATIONAL_HEURISTIC: float = 0.20
WEIGHT_SHARPNESS:             float = 0.10
WEIGHT_SCENE_DURATION:        float = 0.10

# Tuning constants
MAX_SCENE_DURATION_MS: float = 60_000.0   # Normalise duration against 60 s
MAX_OCR_CHARS:         float = 800.0       # Normalise OCR text length
BLUR_SCORE_CAP:        float = 1_000.0     # Normalise sharpness score

# Regex patterns for educational content heuristics
_CODE_PATTERN   = re.compile(r"(def |class |import |#include|<[a-z]|{|}|;$|\(\))", re.M)
_EQUATION_PATTERN = re.compile(r"[=+\-*/\\∑∫∂√≈≤≥±]+")
_BULLET_PATTERN = re.compile(r"^[\s]*[•\-\*\d\.]+\s", re.M)


def _ocr_richness_score(clean_text: str) -> float:
    """
    Score based on the volume of useful text in the frame.
    Normalised against MAX_OCR_CHARS.
    """
    if not clean_text:
        return 0.0
    char_count = len(clean_text.strip())
    return min(char_count / MAX_OCR_CHARS, 1.0)


def _educational_heuristic_score(clean_text: str) -> float:
    """
    Bonus score when the slide appears to contain educational content:
    code blocks, mathematical equations, or bullet lists.
    """
    if not clean_text:
        return 0.0

    score = 0.0
    if _CODE_PATTERN.search(clean_text):
        score += 0.4
    if _EQUATION_PATTERN.search(clean_text):
        score += 0.3
    if _BULLET_PATTERN.search(clean_text):
        score += 0.3
    return min(score, 1.0)


def _sharpness_score(blur_score: float) -> float:
    """Normalise the Laplacian variance to a 0–1 scale."""
    if blur_score <= 0:
        return 0.0
    return min(blur_score / BLUR_SCORE_CAP, 1.0)


def _duration_score(duration_ms: float) -> float:
    """Longer scenes are generally more important content."""
    if duration_ms <= 0:
        return 0.0
    return min(duration_ms / MAX_SCENE_DURATION_MS, 1.0)


def compute_frame_score(frame: Dict[str, Any]) -> float:
    """
    Compute the visual importance score for a single frame.

    Args:
        frame: Dict containing optional keys:
               - clean_text (str)
               - transcript_similarity (float, 0–1)
               - blur_score (float, Laplacian variance)
               - duration_ms (int)

    Returns:
        Composite importance score in [0.0, 1.0].
    """
    clean_text          = frame.get("clean_text", "") or ""
    transcript_sim      = float(frame.get("transcript_similarity", 0.0))
    blur_score          = float(frame.get("blur_score", 0.0))
    duration_ms         = float(frame.get("duration_ms", 0))

    ocr_richness        = _ocr_richness_score(clean_text)
    edu_heuristic       = _educational_heuristic_score(clean_text)
    sharpness           = _sharpness_score(blur_score)
    duration            = _duration_score(duration_ms)

    score = (
        WEIGHT_TRANSCRIPT_SIMILARITY * transcript_sim
        + WEIGHT_OCR_RICHNESS          * ocr_richness
        + WEIGHT_EDUCATIONAL_HEURISTIC * edu_heuristic
        + WEIGHT_SHARPNESS             * sharpness
        + WEIGHT_SCENE_DURATION        * duration
    )

    return round(min(max(score, 0.0), 1.0), 4)


def rank_and_select_frames(
    frames: List[Dict[str, Any]],
    top_n: int = 1,
) -> List[Dict[str, Any]]:
    """
    Rank frames by their composite importance score and mark the top N as selected.

    Args:
        frames: List of enriched frame dicts (post-blur-filter, post-dedup, post-OCR).
        top_n:  Number of frames to mark as selected per call.
                For per-transcript-chunk selection, pass frames for that chunk only.

    Returns:
        The same list, each dict enriched with:
            - 'visual_importance_score' (float)
            - 'is_selected' (bool)
        Sorted by score descending.
    """
    if not frames:
        return []

    scored: List[Dict[str, Any]] = []
    for f in frames:
        score = compute_frame_score(f)
        scored.append({**f, "visual_importance_score": score, "is_selected": False})

    scored.sort(key=lambda x: x["visual_importance_score"], reverse=True)

    for i in range(min(top_n, len(scored))):
        scored[i]["is_selected"] = True

    logger.debug(
        "Frame scoring complete: top score=%.4f, selected=%d of %d",
        scored[0]["visual_importance_score"] if scored else 0.0,
        min(top_n, len(scored)),
        len(scored),
    )
    return scored
