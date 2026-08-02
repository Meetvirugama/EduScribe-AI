"""
Batch ranking and metadata trimming service.
"""
import logging
from itertools import groupby
from typing import List, Dict, Any
from services.vision.scoring.feature_extractor import extract_features
from services.vision.scoring.importance_scorer import calculate_score

logger = logging.getLogger(__name__)


def rank_and_trim_frames(frames: List[Dict[str, Any]], top_n: int = 1) -> List[Dict[str, Any]]:
    """
    Scores and selects the best top_n frames **per scene**, not globally.

    Previously this sorted all frames together and picked the top N across
    the entire video — meaning a 100-scene lecture would have only 1 frame
    marked as selected. This fix groups by scene_number first, then applies
    top_n independently within each group.

    Args:
        frames:  List of frame dicts from OCR/transcript matching stages.
        top_n:   Number of frames to select per scene (default: 1).

    Returns:
        All frames with `is_selected=True` on the top_n per scene.
    """
    if not frames:
        return []

    scored_frames = []
    for f in frames:
        features = extract_features(f)
        score = calculate_score(features)

        # Trim heavy/unnecessary metadata, preserving schema keys for DB insertion
        trimmed = {
            "scene_number": f.get("scene_number"),
            "timestamp_ms": f.get("timestamp_ms"),
            "frame_path": f.get("frame_path"),
            "duration_ms": f.get("duration_ms"),
            "blur_score": f.get("blur_score"),
            "phash": f.get("phash"),
            "raw_text": f.get("raw_text"),
            "clean_text": f.get("clean_text"),
            "average_confidence": f.get("average_confidence"),
            "transcript_similarity": f.get("transcript_similarity"),
            "visual_importance_score": score,
            "is_selected": False,
        }
        scored_frames.append(trimmed)

    # Sort by scene_number first so groupby works correctly, then by score desc within each scene.
    # We use a stable two-key sort: primary=scene_number, secondary=score desc.
    scored_frames.sort(key=lambda x: (x["scene_number"] or 0, -(x["visual_importance_score"] or 0.0)))

    total_selected = 0
    result: List[Dict[str, Any]] = []

    # Group by scene and mark the top_n highest-scoring frames per group
    for scene_num, scene_iter in groupby(scored_frames, key=lambda x: x["scene_number"]):
        scene_frames = list(scene_iter)
        # Within each scene, frames are already sorted by score descending (from sort above)
        for i, frame in enumerate(scene_frames):
            if i < top_n:
                frame["is_selected"] = True
                total_selected += 1
            result.append(frame)

    logger.info(
        "Ranked %d frames across %d scenes. Selected %d (top_n=%d per scene). "
        "Top score: %.4f",
        len(result),
        len(set(f["scene_number"] for f in result)),
        total_selected,
        top_n,
        max((f["visual_importance_score"] or 0.0) for f in result) if result else 0.0,
    )

    return result
