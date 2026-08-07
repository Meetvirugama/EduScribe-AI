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
    GenericTextOutput
)

class SchemaRegistry:
    """
    Maps LLM tasks to their strict Pydantic schemas.
    """
    
    _registry: dict[TaskType, Type[BaseModel]] = {
        TaskType.LECTURE_ANALYSIS: LectureAnalysis,
        TaskType.TOPIC_DETECTION: TopicList,
        TaskType.SUBTOPIC_DETECTION: SubtopicList,
        TaskType.KNOWLEDGE_GAP_ANALYSIS: KnowledgeGap,
        TaskType.DETAILED_EXPLANATION_GEN: SubtopicExplanation,
        TaskType.EXAMPLE_GENERATION: ExampleSet,
        TaskType.QUIZ_GENERATION: QuizSet,
        TaskType.FLASHCARD_GENERATION: FlashcardSet,
        TaskType.MIND_MAP_GENERATION: MindMap,
    }

    @classmethod
    def get_schema(cls, task: TaskType) -> Type[BaseModel]:
        """
        Returns the expected Pydantic schema for the given task.
        Falls back to GenericTextOutput for unstructured responses.
        """
        return cls._registry.get(task, GenericTextOutput)
