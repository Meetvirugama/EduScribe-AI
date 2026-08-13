from typing import Dict, Any, List

class ParserService:
    """
    Parses and validates the raw payload structure before canonicalization.
    Detects fatal flaws.
    """
    
    @staticmethod
    def parse(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        raw_segments = payload.get("raw_segments")
        
        if not raw_segments:
            raise ValueError("CAPTION_PARSE_FAILED: No raw segments found in payload")
            
        if not isinstance(raw_segments, list):
            raise ValueError("CAPTION_PARSE_FAILED: raw_segments is not a list")
            
        # Validate that basic fields exist in at least the first segment
        if len(raw_segments) > 0:
            first = raw_segments[0]
            if "text" not in first or "start" not in first or "duration" not in first:
                raise ValueError("CAPTION_PARSE_FAILED: Malformed segment structure")
                
        return raw_segments
