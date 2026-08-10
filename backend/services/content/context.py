from dataclasses import dataclass, field
from typing import List, Dict, Any
from schemas.content import Concept, Topic, Definition, LectureInput, LectureState

@dataclass
class LectureContext:
    """
    Deprecated: Transitioning to separate LectureInput and LectureState.
    This class combines them for backward compatibility.
    """
    input: LectureInput
    state: LectureState = field(default_factory=LectureState)

    # Backward compatibility properties
    @property
    def transcript(self) -> str: return self.input.transcript
    
    @property
    def segments(self) -> List[Dict[str, Any]]: return self.input.segments
    
    @property
    def metadata(self) -> Dict[str, Any]: return self.input.metadata
    
    @property
    def frames(self) -> List[Dict[str, Any]]: return self.input.frames

    @property
    def concepts(self) -> List[Concept]: return self.state.concepts
    
    @concepts.setter
    def concepts(self, val: List[Concept]): self.state.concepts = val
    
    @property
    def topics(self) -> List[Dict[str, Any]]: return self.state.topics
    
    @topics.setter
    def topics(self, val: List[Dict[str, Any]]): self.state.topics = val
    
    @property
    def definitions(self) -> List[Dict[str, Any]]: return self.state.definitions
    
    @definitions.setter
    def definitions(self, val: List[Dict[str, Any]]): self.state.definitions = val
    
    @property
    def status(self) -> Dict[str, Any]: return self.state.status
    
    @property
    def errors(self) -> Dict[str, str]: return self.state.errors
