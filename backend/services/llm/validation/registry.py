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
    ConceptsOutput,
    LearningObjectivesOutput,
    PrerequisitesOutput,
    DifficultyOutput,
    DefinitionsOutput,
    StepByStepOutput,
    ApplicationsOutput,
    QAOutput,
    RevisionSheetOutput,
    TopicNoteWritingOutput,
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
        TaskType.QUIZ_GENERATION: QuizSet,
        TaskType.FLASHCARD_GENERATION: FlashcardSet,
        TaskType.MIND_MAP_GENERATION: MindMap,

        # ── Phase 1 — Notes pipeline schemas ─────────────────────────────────
        TaskType.DETAILED_NOTES: GenericTextOutput,
        TaskType.TOPIC_NOTE_WRITING: TopicNoteWritingOutput,
        TaskType.NOTE_REPAIR: TopicNoteWritingOutput,

        # ── Phase 2 — Content understanding schemas ──────────────────────────
        TaskType.CONCEPT_EXTRACTION: ConceptsOutput,

        # ── Phase 3 — Knowledge enrichment schemas ───────────────────────────
        TaskType.DEFINITION_GENERATION: DefinitionsOutput,

        # ── Phase 5 – Assessment & support schemas ───────────────────────────

        # ── Phase 6 – Note Organization ────────────────────────────
        TaskType.REVISION_GENERATION: RevisionSheetOutput,

        # ── Phase 7 – QA & verification schemas ──────────────────────────────
    }

    @classmethod
    def get_schema(cls, task: TaskType) -> Type[BaseModel]:
        """
        Returns the expected Pydantic schema for the given task.
        Falls back to GenericTextOutput for tasks without a strict schema.
        """
        return cls._registry.get(task, GenericTextOutput)


