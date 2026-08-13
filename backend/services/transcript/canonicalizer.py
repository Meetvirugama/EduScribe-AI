import html
from typing import Dict, Any, List
from .models import CanonicalTranscript, TranscriptSegment

class CanonicalizerService:
    """
    Converts the parsed raw segments into the standard CanonicalTranscript model.
    Applies conservative text normalization (HTML decoding, whitespace trimming).
    """
    
    @staticmethod
    def canonicalize(payload: Dict[str, Any], raw_segments: List[Dict[str, Any]]) -> CanonicalTranscript:
        canonical_segments = []
        
        for idx, seg in enumerate(raw_segments):
            # Parse timing
            start = float(seg.get("start", 0.0))
            duration = float(seg.get("duration", 0.0))
            end = start + duration
            
            # Normalize text
            raw_text = seg.get("text", "")
            # 1. HTML entity decoding
            text = html.unescape(raw_text)
            # 2. Replace weird whitespaces and newlines
            text = text.replace("\n", " ").replace("\r", "")
            # 3. Strip edges
            text = text.strip()
            
            # Create standard segment
            canonical_segments.append(TranscriptSegment(
                index=idx,
                start=start,
                end=end,
                text=text,
                language=payload.get("language", "unknown"),
                speaker=None,
                confidence=1.0 # Caption API doesn't provide confidence
            ))
            
        return CanonicalTranscript(
            video_id=payload.get("video_id", "unknown"),
            source_type=payload.get("source_type", "unknown"),
            language=payload.get("language", "unknown"),
            segments=canonical_segments
        )
