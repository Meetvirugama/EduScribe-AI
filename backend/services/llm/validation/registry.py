"""
services/llm/validation/registry.py — Expanded Schema Registry

Maps every actively-used TaskType to a strict Pydantic schema.
Tasks not listed here fall back to GenericTextOutput (acceptable for
non-critical or rarely-used tasks).

Issue Resolved: #5 (LLM output validation expansion)
"""
from typing import Type
from pydantic import BaseModel
from ..model_selector import TaskType
from .schemas.core import (
    LectureAnalysis,
    TopicList,
    SubtopicList,
    KnowledgeGap,
    SubtopicExplanation,
    ExampleSet,
    QuizSet,
    FlashcardSet,
    MindMap,
    GenericTextOutput,
)
from .schemas.notes import (
    TopicsAndNotesOutput,
    ConceptsOutput,
    LearningObjectivesOutput,
    PrerequisitesOutput,
    DifficultyOutput,
    DefinitionsOutput,
    StepByStepOutput,
    ApplicationsOutput,
    ExamplesDetailedOutput,
    MisconceptionsOutput,
    AssessmentsOutput,
    LearningSupportOutput,
    LearningPathOutput,
    GlossaryOutput,
    QAOutput,
)


class SchemaRegistry:
    """
    Maps LLM tasks to their strict Pydantic schemas.

    Priority order for tasks.py active calls:
      Phase 1  — DETAILED_NOTES, TOPIC_DETECTION
      Phase 2  — CONCEPT_EXTRACTION, LEARNING_OBJECTIVE_DETECTION,
                 PREREQUISITE_DETECTION, DIFFICULTY_CLASSIFICATION
      Phase 3  — DEFINITION_GENERATION, STEP_BY_STEP_EXPLANATION,
                 REAL_WORLD_APPLICATIONS, EXAMPLE_GENERATION,
                 KNOWLEDGE_GAP (misconceptions)
      Phase 5  — (QUIZ_GENERATION, FLASHCARD_GENERATION covered by core schemas)
      Phase 7  — FACT_CHECKING (QA verification), MIND_MAP_GENERATION
    """

    _registry: dict[TaskType, Type[BaseModel]] = {
        # ── Core schemas (from original registry) ────────────────────────────
        TaskType.LECTURE_ANALYSIS:          LectureAnalysis,
        TaskType.TOPIC_DETECTION:           TopicList,
        TaskType.SUBTOPIC_DETECTION:        SubtopicList,
        TaskType.KNOWLEDGE_GAP_ANALYSIS:    KnowledgeGap,
        TaskType.DETAILED_EXPLANATION_GEN:  SubtopicExplanation,
        TaskType.EXAMPLE_GENERATION:        ExampleSet,
        TaskType.QUIZ_GENERATION:           QuizSet,
        TaskType.FLASHCARD_GENERATION:      FlashcardSet,
        TaskType.MIND_MAP_GENERATION:       MindMap,

        # ── Phase 1 — Notes pipeline schemas ─────────────────────────────────
        TaskType.DETAILED_NOTES:            TopicsAndNotesOutput,

        # ── Phase 2 — Content understanding schemas ───────────────────────────
        TaskType.CONCEPT_EXTRACTION:                ConceptsOutput,
        TaskType.KEYWORD_EXTRACTION:                ConceptsOutput,
        TaskType.LEARNING_OBJECTIVE_DETECTION:      LearningObjectivesOutput,
        TaskType.PREREQUISITE_DETECTION:            PrerequisitesOutput,
        TaskType.DEPENDENCY_DETECTION:              PrerequisitesOutput,
        TaskType.DIFFICULTY_CLASSIFICATION:         DifficultyOutput,

        # ── Phase 3 — Knowledge enrichment schemas ────────────────────────────
        TaskType.DEFINITION_GENERATION:             DefinitionsOutput,
        TaskType.STEP_BY_STEP_EXPLANATION:          StepByStepOutput,
        TaskType.REAL_WORLD_APPLICATIONS:           ApplicationsOutput,
        TaskType.INDUSTRY_USE_CASES:                ApplicationsOutput,

        # ── Phase 5 — Assessment & support schemas ────────────────────────────
        TaskType.LEARNING_OBJECTIVE_DETECTION:      LearningObjectivesOutput,

        # ── Phase 7 — QA & verification schemas ──────────────────────────────
        TaskType.FACT_CHECKING:                     QAOutput,
    }

    @classmethod
    def get_schema(cls, task: TaskType) -> Type[BaseModel]:
        """
        Returns the expected Pydantic schema for the given task.
        Falls back to GenericTextOutput for tasks without a strict schema.
        """
        return cls._registry.get(task, GenericTextOutput)

    @classmethod
    def has_strict_schema(cls, task: TaskType) -> bool:
        """Return True if the task has a schema stricter than GenericTextOutput."""
        return task in cls._registry
