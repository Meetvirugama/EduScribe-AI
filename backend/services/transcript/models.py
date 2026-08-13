from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class TranscriptSegment:
    index: int
    start: float
    end: float
    text: str
    language: str
    speaker: Optional[str] = None
    confidence: float = 1.0


@dataclass
class CanonicalTranscript:
    video_id: str
    source_type: str  # e.g., 'manual', 'automatic', 'stt'
    language: str
    segments: List[TranscriptSegment] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_duration(self) -> float:
        if not self.segments:
            return 0.0
        return self.segments[-1].end

    @property
    def full_text(self) -> str:
        return " ".join([s.text for s in self.segments if s.text])
