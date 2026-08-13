from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING


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
    confidence: float = Field(default=1.0)
    topic_association: Optional[str] = None


class Topic(BaseModel):
    model_config = ConfigDict(extra="ignore")
    title: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    notes_markdown: Optional[str] = None
    key_takeaways: List[str] = Field(default_factory=list)
    source: List[SourceReference] = Field(default_factory=list)
    confidence: float = Field(default=1.0)


class Definition(BaseModel):
    model_config = ConfigDict(extra="ignore")
    term: str
    definition: str
    source: List[SourceReference] = Field(default_factory=list)
    importance: Optional[str] = None
    confidence: float = Field(default=1.0)
    topic_association: Optional[str] = None


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
    topic_association: Optional[str] = None
    timestamp: Optional[float] = None
    source: List[SourceReference] = Field(default_factory=list)
    importance: Optional[str] = None
    confidence: float = Field(default=1.0)


class Example(BaseModel):
    model_config = ConfigDict(extra="ignore")
    title: str
    problem: str
    explanation: Optional[str] = None
    solution: Optional[str] = None
    topic_association: Optional[str] = None
    timestamp: Optional[float] = None
    source: List[SourceReference] = Field(default_factory=list)
    importance: Optional[str] = None
    confidence: float = Field(default=1.0)


class KeyPoint(BaseModel):
    model_config = ConfigDict(extra="ignore")
    text: str
    importance: Optional[str] = None
    category: Optional[str] = None
    topic_association: Optional[str] = None
    timestamp: Optional[float] = None
    source: List[SourceReference] = Field(default_factory=list)
    confidence: float = Field(default=1.0)


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

    # Phase 1 output — Unified Markdown (transcript + vision merged)
    unified_md: str = ""

    # Phase 3a output — Enriched Unified Markdown (unified_md + all extractions injected)
    knowledge_compilation_doc: str = ""

    # Phase 3b output — Full Detailed Learning Note (generated from enriched chunks)
    detailed_notes_md: str = ""

    # Phase 3 redesign — ephemeral in-memory objects (not serialised by default)
    # EvidenceStore built from transcript segments + OCR frames
    evidence_store: Optional[Any] = field(default=None)
    # KnowledgeGraph built from KnowledgeUnits + Relationships
    knowledge_graph: Optional[Any] = field(default=None)

    # Status tracking per service/phase
    status: Dict[str, ServiceStatus] = field(default_factory=dict)

    # Errors and metadata
    errors: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, GenerationMetadata] = field(default_factory=dict)

class QualityIssue(BaseModel):
    model_config = ConfigDict(extra="ignore")
    type: str
    severity: str
    section: str
    problem: str
    evidence: str
    fix: str

class QualityReport(BaseModel):
    model_config = ConfigDict(extra="ignore")
    score: int
    issues: List[QualityIssue] = Field(default_factory=list)
