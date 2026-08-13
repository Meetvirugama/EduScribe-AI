"""
In-memory cache for parsed transcript data and binary search indexes.
"""
from typing import Optional
from services.vision.transcript.index import TranscriptIndex


class TranscriptCache:
    """
    Transcript parsing and indexing should happen once.
    Repeated processing wastes CPU.
    """

    def __init__(self):
        self._cache = {}

    def get_index(self, video_id: str) -> Optional[TranscriptIndex]:
        return self._cache.get(video_id)

    def set_index(self, video_id: str, index: TranscriptIndex):
        self._cache[video_id] = index

    def clear(self):
        self._cache.clear()


transcript_cache = TranscriptCache()
