from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum
import re
from ..base_schema import BaseLLMOutput

class QuestionType(str, Enum):
    MCQ = "mcq"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"
    HOTS = "hots"

class MindMapFormat(str, Enum):
    MERMAID = "mermaid"
    MARKDOWN_TREE = "markdown_tree"
    NESTED_BULLETS = "nested_bullets"

# ---------------------------------------------------------
# Stage 1 — Lecture Analysis
# ---------------------------------------------------------
class LectureAnalysis(BaseLLMOutput):
    subject: str
    difficulty: int = Field(ge=1, le=5)
    prerequisites: List[str]
    teaching_style: str
    primary_objectives: List[str]
    estimated_topics: int = Field(ge=1)

# ---------------------------------------------------------
# Stage 2 — Topic Detection
# ---------------------------------------------------------
class Topic(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")
    title: str
    start_time: str
    end_time: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    
    @field_validator("start_time", "end_time")
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        if not re.match(r"^\d{2}:\d{2}:\d{2}(\.\d+)?$", v):
            raise ValueError("Timestamp must be in HH:MM:SS or HH:MM:SS.sss format")
        return v

class TopicList(BaseLLMOutput):
    topics: List[Topic]

# ---------------------------------------------------------
# Stage 3 — Subtopic Detection
# ---------------------------------------------------------
class SubtopicList(BaseLLMOutput):
    topic: str
    subtopics: List[str] = Field(min_length=1)

# ---------------------------------------------------------
# Stage 4 — Knowledge Gap Analysis
# ---------------------------------------------------------
class KnowledgeGap(BaseLLMOutput):
    missing_definitions: List[str]
    missing_prerequisites: List[str]
    implicit_reasoning: List[str]
    potential_misconceptions: List[str]

# ---------------------------------------------------------
# Stage 5 — Explanation
# ---------------------------------------------------------
class SubtopicExplanation(BaseLLMOutput):
    subtopic: str
    definition: str
    motivation: str
    step_by_step: str
    worked_example: str
    common_mistakes: List[str]
    key_takeaways: List[str]
    frame_references: List[str]
    
    @property
    def word_count(self) -> int:
        full_text = " ".join([
            self.definition, self.motivation, self.step_by_step, 
            self.worked_example, " ".join(self.common_mistakes), 
            " ".join(self.key_takeaways)
        ])
        return len(full_text.split())

# ---------------------------------------------------------
# Stage 6 — Example Generation
# ---------------------------------------------------------
class ExampleSet(BaseLLMOutput):
    subtopic: str
    simple_examples: List[str]
    intermediate_examples: List[str]
    real_world_applications: List[str]
    numerical_examples: Optional[List[str]] = None
    programming_examples: Optional[List[str]] = None
    visual_examples: Optional[List[str]] = None

# ---------------------------------------------------------
# Stage 9 — Quiz Generation
# ---------------------------------------------------------
class QuizQuestion(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")
    question: str
    question_type: QuestionType
    options: Optional[List[str]] = None
    correct_answer: str
    explanation: str
    difficulty: int = Field(ge=1, le=5)

class QuizSet(BaseLLMOutput):
    topic: str
    subtopic: str
    questions: List[QuizQuestion]

# ---------------------------------------------------------
# Extras
# ---------------------------------------------------------
class Flashcard(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")
    front: str
    back: str
    tags: Optional[List[str]] = None

class FlashcardSet(BaseLLMOutput):
    topic: str
    flashcards: List[Flashcard]

class MindMap(BaseLLMOutput):
    topic: str
    format: MindMapFormat
    content: str

class GenericTextOutput(BaseLLMOutput):
    """Fallback schema for tasks that return unstructured text."""
    text: str
