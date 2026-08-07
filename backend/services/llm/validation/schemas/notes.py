"""
services/llm/validation/schemas/notes.py — Strict Output Schemas for Notes Pipeline

Provides Pydantic models for all 15 actively used TaskTypes in tasks.py.
Replacing GenericTextOutput fallbacks with strict schemas prevents invalid,
incomplete, or hallucinated outputs from propagating through the pipeline.

Issue Resolved: #5 (LLM output validation expansion)
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict

from ..base_schema import BaseLLMOutput


# ---------------------------------------------------------------------------
# Shared sub-models
# ---------------------------------------------------------------------------

class BloomLevel(str, Enum):
    REMEMBER   = "remember"
    UNDERSTAND = "understand"
    APPLY      = "apply"
    ANALYZE    = "analyze"
    EVALUATE   = "evaluate"
    CREATE     = "create"


class ImportanceLevel(str, Enum):
    HIGH   = "high"
    MEDIUM = "medium"
    LOW    = "low"


# ---------------------------------------------------------------------------
# Phase 1 — Topics & Notes  (generate_topics_and_notes)
# ---------------------------------------------------------------------------

class Citation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")
    timestamp: Optional[str] = None        # HH:MM:SS
    frame_path: Optional[str] = None
    source: str = "transcript"             # transcript | ocr

    @field_validator("timestamp")
    @classmethod
    def validate_ts(cls, v: Optional[str]) -> Optional[str]:
        import re
        if v and not re.match(r"^\d{2}:\d{2}:\d{2}$", v):
            raise ValueError("Timestamp must be HH:MM:SS")
        return v


class TopicNote(BaseModel):
    model_config = ConfigDict(extra="ignore")
    title: str = Field(min_length=1)
    start_time: str = "00:00:00"
    end_time: str = "00:00:00"
    notes_markdown: str = Field(min_length=10)
    key_takeaways: List[str] = Field(default_factory=list)
    citations: List[Citation] = Field(default_factory=list)


class TopicsAndNotesOutput(BaseLLMOutput):
    summary: str = Field(min_length=20)
    topics: List[TopicNote] = Field(min_length=1)


# ---------------------------------------------------------------------------
# Phase 2 — Concepts & Keywords  (extract_concepts_and_keywords)
# ---------------------------------------------------------------------------

class ConceptItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str
    category: str = ""
    importance: ImportanceLevel = ImportanceLevel.MEDIUM
    brief_description: str = ""


class ConceptsOutput(BaseLLMOutput):
    concepts: List[ConceptItem] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    key_phrases: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Phase 2 — Learning Objectives  (detect_learning_objectives)
# ---------------------------------------------------------------------------

class LearningObjectiveItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    objective: str
    bloom_level: BloomLevel = BloomLevel.UNDERSTAND
    topic: str = ""


class LearningObjectivesOutput(BaseLLMOutput):
    learning_objectives: List[LearningObjectiveItem] = Field(default_factory=list)
    target_audience: str = ""
    estimated_study_time_minutes: int = Field(default=0, ge=0)


# ---------------------------------------------------------------------------
# Phase 2 — Prerequisites  (detect_prerequisites_and_dependencies)
# ---------------------------------------------------------------------------

class PrerequisiteItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    topic: str
    importance: ImportanceLevel = ImportanceLevel.MEDIUM
    description: str = ""


class PrerequisitesOutput(BaseLLMOutput):
    prerequisites: List[PrerequisiteItem] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    recommended_background: str = ""


# ---------------------------------------------------------------------------
# Phase 2 — Difficulty Classification  (classify_difficulty)
# ---------------------------------------------------------------------------

class DifficultyOutput(BaseLLMOutput):
    overall_difficulty: int = Field(ge=1, le=5)
    difficulty_label: str = "intermediate"     # beginner | intermediate | advanced
    reasoning: str = ""
    topic_difficulties: List[Dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Phase 3 — Definitions  (generate_definitions)
# ---------------------------------------------------------------------------

class DefinitionItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    term: str
    definition: str
    example: str = ""
    related_terms: List[str] = Field(default_factory=list)


class DefinitionsOutput(BaseLLMOutput):
    definitions: List[DefinitionItem] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Phase 3 — Step-by-Step Explanations  (generate_step_by_step_explanations)
# ---------------------------------------------------------------------------

class StepItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    step_number: int = Field(ge=1)
    title: str
    explanation: str
    example: str = ""
    common_mistake: str = ""


class StepByStepOutput(BaseLLMOutput):
    topic: str = ""
    steps: List[StepItem] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Phase 3 — Real-World Applications  (generate_real_world_applications)
# ---------------------------------------------------------------------------

class ApplicationItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    domain: str
    application: str
    example: str = ""
    impact: str = ""


class ApplicationsOutput(BaseLLMOutput):
    applications: List[ApplicationItem] = Field(default_factory=list)
    industry_examples: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Phase 3 — Examples  (generate_examples)
# ---------------------------------------------------------------------------

class ExamplesDetailedOutput(BaseLLMOutput):
    examples: List[Dict[str, Any]] = Field(default_factory=list)
    worked_examples: List[Dict[str, Any]] = Field(default_factory=list)
    counter_examples: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Phase 3 — Misconceptions  (detect_misconceptions_and_edge_cases)
# ---------------------------------------------------------------------------

class MisconceptionItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    misconception: str
    correction: str
    explanation: str = ""


class MisconceptionsOutput(BaseLLMOutput):
    misconceptions: List[MisconceptionItem] = Field(default_factory=list)
    edge_cases: List[Dict[str, Any]] = Field(default_factory=list)
    common_errors: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Phase 5 — Assessments  (generate_assessments)
# ---------------------------------------------------------------------------

class AssessmentQuestion(BaseModel):
    model_config = ConfigDict(extra="ignore")
    question: str
    question_type: str = "mcq"             # mcq | true_false | fill_blank | hots
    options: Optional[List[str]] = None
    correct_answer: str
    explanation: str = ""
    difficulty: int = Field(default=3, ge=1, le=5)


class AssessmentsOutput(BaseLLMOutput):
    quiz_questions: List[AssessmentQuestion] = Field(default_factory=list)
    flashcards: List[Dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Phase 5 — Learning Support  (generate_learning_support)
# ---------------------------------------------------------------------------

class LearningSupportOutput(BaseLLMOutput):
    study_tips: List[str] = Field(default_factory=list)
    recommended_resources: List[Dict[str, Any]] = Field(default_factory=list)
    practice_exercises: List[str] = Field(default_factory=list)
    memory_aids: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Phase 5 — Learning Path  (generate_learning_path)
# ---------------------------------------------------------------------------

class LearningPathStep(BaseModel):
    model_config = ConfigDict(extra="ignore")
    step: int = Field(ge=1)
    title: str
    description: str
    estimated_time_minutes: int = Field(default=30, ge=1)
    resources: List[str] = Field(default_factory=list)


class LearningPathOutput(BaseLLMOutput):
    path_title: str = ""
    total_estimated_time_minutes: int = Field(default=0, ge=0)
    steps: List[LearningPathStep] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Phase 5 — Glossary  (generate_glossary)
# ---------------------------------------------------------------------------

class GlossaryOutput(BaseLLMOutput):
    terms: List[DefinitionItem] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Phase 7 — QA Fact Verification  (verify_facts)
# ---------------------------------------------------------------------------

class QAWarning(BaseModel):
    model_config = ConfigDict(extra="ignore")
    issue: str
    correction: str
    severity: str = "low"   # low | medium | high
    timestamp: Optional[str] = None


class QAOutput(BaseLLMOutput):
    qa_warnings: List[QAWarning] = Field(default_factory=list)
    overall_accuracy_score: float = Field(default=1.0, ge=0.0, le=1.0)
    verified_facts: List[str] = Field(default_factory=list)
