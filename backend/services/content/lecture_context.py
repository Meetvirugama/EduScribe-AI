from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class LectureContext:
    """
    Shared state object representing a lecture throughout the generation pipeline.
    Prevents passing the entire raw transcript to every service, and allows for 
    reusing intermediate results like topics and definitions.
    """
    transcript: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Intermediate results that can be reused
    topics: List[Dict[str, Any]] = field(default_factory=list)
    concepts: List[Dict[str, Any]] = field(default_factory=list)
    definitions: List[Dict[str, Any]] = field(default_factory=list)
    
    # Additional context
    difficulty: int = 3
    frames: List[Dict[str, Any]] = field(default_factory=list)
