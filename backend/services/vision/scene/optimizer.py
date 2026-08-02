"""
Post-processing tools to clean and optimize scene boundaries.
"""
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def merge_short_scenes(scenes: List[Dict[str, Any]], min_duration_ms: int = 2000) -> List[Dict[str, Any]]:
    """
    Short scenes are merged because tiny segments increase the
    number of frames passed into OCR and ranking stages.
    """
    if not scenes:
        return []
        
    merged = [scenes[0].copy()]
    for current in scenes[1:]:
        prev = merged[-1]
        
        # If the previous scene was too short, merge this current one into it
        if prev["duration_ms"] < min_duration_ms:
            prev["end_time_ms"] = current["end_time_ms"]
            prev["duration_ms"] = prev["end_time_ms"] - prev["start_time_ms"]
            prev["frame_count"] += current.get("frame_count", 0)
        else:
            merged.append(current.copy())
            
    # Re-number
    for i, s in enumerate(merged):
        s["scene_number"] = i + 1
        
    logger.debug("Merged %d raw scenes down to %d optimized scenes", len(scenes), len(merged))
    return merged

def generate_adaptive_fallback(video_path: str) -> List[Dict[str, Any]]:
    """
    If no scene changes are found, we chunk the video.
    Fixed 30s chunks are not optimal for long static lectures.
    We adapt chunk size based on video length (60-120s for long videos).
    """
    import cv2
    
    cap = cv2.VideoCapture(video_path)
    try:
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
        duration_ms = int((frame_count / fps) * 1000)
    finally:
        cap.release()

    if duration_ms <= 0:
        return []

    # Adaptive chunking logic
    if duration_ms > 3600000: # > 1 hour
        chunk_duration_ms = 120000 # 2 mins
    elif duration_ms > 600000: # > 10 mins
        chunk_duration_ms = 60000 # 1 min
    else:
        chunk_duration_ms = 30000 # 30s

    scenes = []
    start_ms = 0
    scene_num = 1
    
    while start_ms < duration_ms:
        end_ms = min(start_ms + chunk_duration_ms, duration_ms)
        scenes.append({
            "scene_number": scene_num,
            "start_time_ms": start_ms,
            "end_time_ms": end_ms,
            "duration_ms": end_ms - start_ms,
            "frame_count": int((end_ms - start_ms) * fps / 1000),
            "scene_type": "fallback_chunk",
            "detection_version": "v2.0"
        })
        start_ms = end_ms
        scene_num += 1

    return scenes
