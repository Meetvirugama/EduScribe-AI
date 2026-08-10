from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


class ServiceStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SourceReference(BaseModel):
    model_config = ConfigDict(extra="ignore")
    chunk_id: str
    start: Optional[int] = None
    end: Optional[int] = None
    timestamp_start: Optional[float] = None
    timestamp_end: Optional[float] = None


class GenerationMetadata(BaseModel):
    model_config = ConfigDict(extra="ignore")
    task_type: str
    model_name: str
    prompt_version: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Concept(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str
    category: Optional[str] = None
    importance: Optional[str] = None
    brief_description: Optional[str] = None
    source: List[SourceReference] = Field(default_factory=list)


class Topic(BaseModel):
    model_config = ConfigDict(extra="ignore")
    title: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    notes_markdown: Optional[str] = None
    key_takeaways: List[str] = Field(default_factory=list)
    source: List[SourceReference] = Field(default_factory=list)


class Definition(BaseModel):
    model_config = ConfigDict(extra="ignore")
    term: str
    definition: str
    source: List[SourceReference] = Field(default_factory=list)


class Summary(BaseModel):
    model_config = ConfigDict(extra="ignore")
    text: str
    source: List[SourceReference] = Field(default_factory=list)


class FormulaItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str
    expression: str
    variables: Optional[Dict[str, str]] = None
    explanation: Optional[str] = None
    topic: Optional[str] = None
    timestamp: Optional[float] = None
    source: List[SourceReference] = Field(default_factory=list)


class Example(BaseModel):
    model_config = ConfigDict(extra="ignore")
    title: str
    problem: str
    explanation: Optional[str] = None
    solution: Optional[str] = None
    topic: Optional[str] = None
    timestamp: Optional[float] = None
    source: List[SourceReference] = Field(default_factory=list)


class KeyPoint(BaseModel):
    model_config = ConfigDict(extra="ignore")
    text: str
    importance: Optional[str] = None
    category: Optional[str] = None
    topic: Optional[str] = None
    timestamp: Optional[float] = None
    source: List[SourceReference] = Field(default_factory=list)


class Relationship(BaseModel):
    model_config = ConfigDict(extra="ignore")
    from_concept: str
    relationship_type: str
    to_concept: str


@dataclass(frozen=True)
class LectureInput:
    """Immutable input data for the pipeline."""
    transcript: str
    segments: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    frames: List[Dict[str, Any]] = field(default_factory=list)
    difficulty: int = 3


@dataclass
class LectureState:
    """Mutable state containing AI-generated results and pipeline status."""
    topics: List[Topic] = field(default_factory=list)
    concepts: List[Concept] = field(default_factory=list)
    definitions: List[Definition] = field(default_factory=list)
    summaries: List[Summary] = field(default_factory=list)
    formulas_extracted: List[FormulaItem] = field(default_factory=list)
    examples: List[Example] = field(default_factory=list)
    key_points: List[KeyPoint] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)
    important_frames: List[Dict] = field(default_factory=list)

    # CRITICAL-006: These fields were missing, causing pipeline.py to always
    # return {} for quiz/flashcards/mindmap/interview/revision/formula even
    # though the LLM services ran and produced real output.
    quiz: List[Any] = field(default_factory=list)
    flashcards: List[Any] = field(default_factory=list)
    mindmap: Dict[str, Any] = field(default_factory=dict)
    interview: List[Any] = field(default_factory=list)
    revision: Dict[str, Any] = field(default_factory=dict)
    formula: Dict[str, Any] = field(default_factory=dict)

    # Status tracking per service/phase
    status: Dict[str, ServiceStatus] = field(default_factory=dict)

    # Errors and metadata
    errors: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, GenerationMetadata] = field(default_factory=dict)
