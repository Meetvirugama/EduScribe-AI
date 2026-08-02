"""
Extracts structural features from frame metadata.
Caches values to avoid redundant computation.
"""
from typing import Dict, Any

def extract_features(frame: Dict[str, Any]) -> Dict[str, float]:
    """
    Extracts and normalizes features once in O(1) time.
    """
    clean_text = frame.get("clean_text", "") or ""
    
    transcript_sim = float(frame.get("transcript_similarity", 0.0))
    ocr_density = min(len(clean_text.strip()) / 800.0, 1.0)
    
    # Use features previously calculated and cached by OCR stage
    edu_score = 0.0
    if frame.get("has_code"): edu_score += 0.4
    if frame.get("has_equation"): edu_score += 0.3
    if frame.get("has_bullets"): edu_score += 0.3
    
    blur = float(frame.get("blur_score", 0.0))
    sharpness = min(blur / 1000.0, 1.0)
    
    duration = float(frame.get("duration_ms", 0))
    scene_score = min(duration / 60_000.0, 1.0)
    
    return {
        "f_transcript": transcript_sim,
        "f_ocr": ocr_density,
        "f_edu": min(edu_score, 1.0),
        "f_sharpness": sharpness,
        "f_scene": scene_score
    }
