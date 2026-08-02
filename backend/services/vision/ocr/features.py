"""
Generates reusable numerical features from OCR text for downstream ranking.
"""
import re
from typing import Dict, Any

_CODE_PATTERN = re.compile(r"(def |class |import |#include|<[a-z]|{|}|;$|\(\))", re.M)
_EQUATION_PATTERN = re.compile(r"[=+\-*/\\∑∫∂√≈≤≥±]+")
_BULLET_PATTERN = re.compile(r"^[\s]*[•\-\*\d\.]+\s", re.M)

def generate_ocr_features(clean_text: str, avg_conf: float, line_count: int) -> Dict[str, Any]:
    """Generates reusable numerical features for downstream ranking."""
    if not clean_text:
        return {
            "average_confidence": 0.0,
            "line_count": 0,
            "word_count": 0,
            "character_count": 0,
            "has_code": False,
            "has_equation": False,
            "has_bullets": False
        }

    return {
        "average_confidence": round(avg_conf, 4),
        "line_count": line_count,
        "word_count": len(clean_text.split()),
        "character_count": len(clean_text),
        "has_code": bool(_CODE_PATTERN.search(clean_text)),
        "has_equation": bool(_EQUATION_PATTERN.search(clean_text)),
        "has_bullets": bool(_BULLET_PATTERN.search(clean_text))
    }
