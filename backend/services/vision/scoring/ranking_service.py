"""
Batch ranking and metadata trimming service.
"""
import logging
from typing import List, Dict, Any
from services.vision.scoring.feature_extractor import extract_features
from services.vision.scoring.importance_scorer import calculate_score

logger = logging.getLogger(__name__)

def rank_and_trim_frames(frames: List[Dict[str, Any]], top_n: int = 1) -> List[Dict[str, Any]]:
    """
    Scores, sorts in batch, and aggressively trims metadata to save RAM.
    """
    if not frames:
        return []

    scored_frames = []
    for f in frames:
        features = extract_features(f)
        score = calculate_score(features)
        
        # Trim heavy/unnecessary metadata, but preserve schema keys for DB insertion
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
            "is_selected": False
        }
        scored_frames.append(trimmed)

    # Batch sorting minimizes CPU overhead vs repeated sorting
    scored_frames.sort(key=lambda x: x["visual_importance_score"], reverse=True)
    
    for i in range(min(top_n, len(scored_frames))):
        scored_frames[i]["is_selected"] = True
        
    logger.debug(
        "Ranked %d frames. Top score: %.4f",
        len(scored_frames),
        scored_frames[0]["visual_importance_score"] if scored_frames else 0.0
    )
    
    return scored_frames
