"""
In-memory and/or simple cache for scene detection results.
"""
from typing import List, Dict, Any, Optional

class SceneCache:
    """
    Scene results are cached because detecting scenes requires
    reading the entire video. Re-running detection wastes CPU time.
    """
    def __init__(self):
        self._cache = {}
        self.VERSION = "v2.0"

    def get(self, video_id: str) -> Optional[List[Dict[str, Any]]]:
        if video_id in self._cache:
            data = self._cache[video_id]
            if data.get("version") == self.VERSION:
                return data.get("scenes")
        return None

    def set(self, video_id: str, scenes: List[Dict[str, Any]]):
        self._cache[video_id] = {
            "version": self.VERSION,
            "scenes": scenes
        }

    def clear(self):
        self._cache.clear()

scene_cache = SceneCache()
