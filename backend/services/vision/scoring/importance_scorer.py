"""
Applies the visual importance weighting formula using O(1) float operations.
"""
from typing import Dict


def calculate_score(features: Dict[str, float]) -> float:
    """
    Weighted importance score based on cached features.
    No heavy AI or string parsing occurs here.
    """
    score = (
        (features["f_transcript"] * 0.35) +
        (features["f_ocr"] * 0.25) +
        (features["f_edu"] * 0.20) +
        (features["f_sharpness"] * 0.10) +
        (features["f_scene"] * 0.10)
    )
    return round(min(max(score, 0.0), 1.0), 4)
