"""
In-memory cache for OCR results.
"""
from typing import Dict, Any, Optional

class OCRCache:
    """
    In-memory cache to prevent redundant OCR inference on identical paths.
    
    # OCR results are cached because visual ranking may happen multiple
    # times during processing. Re-running OCR would unnecessarily increase
    # GPU utilization.
    """
    def __init__(self):
        self._cache = {}

    def get(self, frame_path: str) -> Optional[Dict[str, Any]]:
        return self._cache.get(frame_path)

    def set(self, frame_path: str, data: Dict[str, Any]):
        self._cache[frame_path] = data

    def clear(self):
        self._cache.clear()

ocr_cache = OCRCache()
