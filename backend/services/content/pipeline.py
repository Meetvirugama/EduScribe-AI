import asyncio
import logging
from typing import Dict, Any, List

from .context import LectureContext
from ..llm.llm_manager import LLMManager
from schemas.content import LectureInput, ServiceStatus

from services.merge.models import MergedLecture, MergedSection

from .topic import TopicService
from .concept import ConceptService
from .definition import DefinitionService
from .example import ExampleService
from .key_point import KeyPointService
from .relationship import RelationshipService

logger = logging.getLogger(__name__)

class ContentPipeline:
    """
    Orchestrates the extraction of knowledge from a MergedLecture.
    It builds a complete LearningContext.
    
    Architecture rule: 
    This pipeline DOES NOT generate artifacts (quiz, flashcards, etc).
    It only builds the structured source of truth (LearningContext).
    """
    def __init__(self, llm_manager: LLMManager):
        self.llm_manager = llm_manager
        
        # Extraction Services
        self.topic_service = TopicService(llm_manager)
        self.concept_service = ConceptService(llm_manager)
        self.definition_service = DefinitionService(llm_manager)
        self.example_service = ExampleService(llm_manager)
        self.key_point_service = KeyPointService(llm_manager)
        self.relationship_service = RelationshipService(llm_manager)

    async def build_learning_context(self, merged_lecture: MergedLecture) -> LectureContext:
        """
        Extracts foundational knowledge from the MergedLecture sequentially section by section,
        and aggregates into a single LearningContext.
        """
        logger.info(f"Starting content extraction pipeline for video {merged_lecture.video_id}")
        
        lecture_input = LectureInput(
            transcript=merged_lecture.full_transcript_text,
            metadata=merged_lecture.metadata,
            segments=merged_lecture.all_transcript_segments,
            frames=[
                {
                    "path": f.frame_path, 
                    "time_sec": f.timestamp_sec, 
                    "ocr": f.ocr_text, 
                    "scene_number": f.scene_number
                } 
                for f in merged_lecture.all_frames
            ]
        )
        context = LectureContext(input=lecture_input)
        
        # Level 1: Foundational extractions (run concurrently)
        await asyncio.gather(
            self.topic_service.execute_with_retry("topic", context, self.topic_service.extract_topics, context),
            self.concept_service.execute_with_retry("concept", context, self.concept_service.extract_concepts, context),
            self.definition_service.execute_with_retry("definition", context, self.definition_service.extract_definitions, context),
            self.example_service.execute_with_retry("example", context, self.example_service.extract_examples, context),
            self.key_point_service.execute_with_retry("key_point", context, self.key_point_service.extract_key_points, context),
        )

        # Level 2: Dependent extractions (Relationships need Concepts)
        if context.status.get("concept") == ServiceStatus.COMPLETED:
            await self.relationship_service.execute_with_retry(
                "relationship", context, self.relationship_service.extract_relationships, context
            )
        else:
            logger.warning("Skipping Relationship extraction because concept extraction failed.")

        return context
