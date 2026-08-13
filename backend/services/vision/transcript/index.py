"""
O(log N) binary search index for Whisper transcript segments.
"""
import bisect
from typing import List, Dict, Any


class TranscriptIndex:
    """
    Transcript segments are sorted by timestamp.
    Binary search avoids scanning every segment for every frame.
    This reduces CPU usage significantly for long videos.
    """

    def __init__(self, segments: List[Dict[str, Any]]):
        self.segments = sorted(segments, key=lambda x: x.get("start", 0.0))
        self.start_times = [float(s.get("start", 0.0)) for s in self.segments]

    def get_context_segments(self, timestamp_ms: int,
                             window: int = 1) -> List[Dict[str, Any]]:
        """
        Retrieves the exact segment for a timestamp, plus adjacent context.
        Speaker explanations may start before or continue after slide changes.
        """
        if not self.segments:
            return []

        timestamp_s = float(timestamp_ms) / 1000.0

        # O(log N) binary search
        idx = bisect.bisect_right(self.start_times, timestamp_s) - 1
        idx = max(0, idx)

        start_idx = max(0, idx - window)
        end_idx = min(len(self.segments), idx + window + 1)

        return self.segments[start_idx:end_idx]
