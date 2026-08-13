from dataclasses import dataclass, field
from typing import List, Dict, Any
from schemas.content import Concept, LectureInput, LectureState


@dataclass
class LectureContext:
    """
    Runtime container for a lecture's input data and extracted knowledge.

    Wraps LectureInput (raw data) and LectureState (extracted results)
    and exposes both as flat properties for convenience across the pipeline.
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
    def definitions(self) -> List[Dict[str, Any]
                                  ]: return self.state.definitions

    @definitions.setter
    def definitions(self, val: List[Dict[str, Any]]
                    ): self.state.definitions = val

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
    def status(self) -> Dict[str, Any]: return self.state.status

    @property
    def errors(self) -> Dict[str, str]: return self.state.errors

    @property
    def unified_md(self) -> str: return self.state.unified_md

    @unified_md.setter
    def unified_md(self, val: str): self.state.unified_md = val

    @property
    def detailed_notes_md(self) -> str: return self.state.detailed_notes_md

    @detailed_notes_md.setter
    def detailed_notes_md(self, val: str): self.state.detailed_notes_md = val

