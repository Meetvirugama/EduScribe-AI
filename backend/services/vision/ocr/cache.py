"""
In-memory LRU cache for OCR results.

Uses cachetools.LRUCache to cap memory usage at 500 entries.
Without eviction, the cache grows unboundedly for long videos
with hundreds of frames (50–200MB of accumulated OCR data).

LRU eviction automatically removes the least-recently-used entries
when the cache is full, keeping memory predictable.
"""
from typing import Dict, Any, Optional

try:
    from cachetools import LRUCache
    _backend = LRUCache(maxsize=500)
    _HAS_CACHETOOLS = True
except ImportError:
    # Graceful fallback: plain dict (unbounded) if cachetools not installed yet
    _backend = {}
    _HAS_CACHETOOLS = False


class OCRCache:
    """
    Thread-safe LRU cache for OCR results.

    OCR results are cached because visual ranking may trigger re-runs
    during processing. Re-running OCR on the same frame would unnecessarily
    increase GPU/CPU utilization.

    With LRU eviction (maxsize=500), the cache holds at most 500 frame
    results before evicting the oldest unused entries, preventing the
    unbounded memory growth seen with plain dicts in long-video processing.
    """

    def get(self, frame_path: str) -> Optional[Dict[str, Any]]:
        return _backend.get(frame_path)

    def set(self, frame_path: str, data: Dict[str, Any]) -> None:
        _backend[frame_path] = data

    def clear(self) -> None:
        _backend.clear()

    @property
    def size(self) -> int:
        return len(_backend)

    @property
    def maxsize(self) -> int:
        return getattr(_backend, "maxsize", -1)


ocr_cache = OCRCache()
