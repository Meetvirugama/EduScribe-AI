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
    def formulas_extracted(self): return self.state.formulas_extracted
    
    @formulas_extracted.setter
    def formulas_extracted(self, val): self.state.formulas_extracted = val
    
    @property
    def examples(self): return self.state.examples
    
    @examples.setter
    def examples(self, val): self.state.examples = val
    
    @property
    def key_points(self): return self.state.key_points
    
    @key_points.setter
    def key_points(self, val): self.state.key_points = val
    
    @property
    def relationships(self): return self.state.relationships
    
    @relationships.setter
    def relationships(self, val): self.state.relationships = val

    @property
    def important_frames(self): return self.state.important_frames

    @important_frames.setter
    def important_frames(self, val): self.state.important_frames = val

    # CRITICAL-006: Proxy properties for the extended LectureState fields
    @property
    def quiz(self): return self.state.quiz

    @quiz.setter
    def quiz(self, val): self.state.quiz = val

    @property
    def flashcards(self): return self.state.flashcards

    @flashcards.setter
    def flashcards(self, val): self.state.flashcards = val

    @property
    def mindmap(self): return self.state.mindmap

    @mindmap.setter
    def mindmap(self, val): self.state.mindmap = val

    @property
    def interview(self): return self.state.interview

    @interview.setter
    def interview(self, val): self.state.interview = val

    @property
    def revision(self): return self.state.revision

    @revision.setter
    def revision(self, val): self.state.revision = val

    @property
    def formula(self): return self.state.formula

    @formula.setter
    def formula(self, val): self.state.formula = val

    @property
    def status(self) -> Dict[str, Any]: return self.state.status

    @property
    def errors(self) -> Dict[str, str]: return self.state.errors
