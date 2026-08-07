import asyncio
import logging
from typing import Dict, Any
from .lecture_context import LectureContext
from ..llm.llm_manager import LLMManager

from .notes_service import NotesService
from .concept_service import ConceptService
from .quiz_service import QuizService
from .flashcard_service import FlashcardService
from .mindmap_service import MindmapService

logger = logging.getLogger(__name__)

class ContentPipeline:
    """
    Orchestrates the execution of domain-specific content services.
    Uses asyncio.gather() to run independent generations concurrently.
    """
    def __init__(self, llm_manager: LLMManager):
        self.llm_manager = llm_manager
        self.notes_service = NotesService(llm_manager)
        self.concept_service = ConceptService(llm_manager)
        self.quiz_service = QuizService(llm_manager)
        self.flashcard_service = FlashcardService(llm_manager)
        self.mindmap_service = MindmapService(llm_manager)

    async def generate_full_content(self, transcript: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Executes the full pipeline for a given transcript.
        Returns a dictionary of all generated content.
        """
        logger.info("Starting concurrent content pipeline...")
        context = LectureContext(transcript=transcript, metadata=metadata or {})
        
        # Step 1: Sequential prerequisites
        # Extract concepts first so downstream tasks can use them if needed.
        await self.concept_service.extract_concepts(context)
        
        # Step 2: Concurrent execution of independent services
        results = await asyncio.gather(
            self.notes_service.generate_notes(context),
            self.quiz_service.generate_quiz(context),
            self.flashcard_service.generate_flashcards(context),
            self.mindmap_service.generate_mindmap(context),
            return_exceptions=True
        )
        
        notes_res, quiz_res, flashcard_res, mindmap_res = results
        
        def _get_result(res, name, default):
            if isinstance(res, Exception):
                logger.error(f"Pipeline step {name} failed: {res}")
                return default
            return res
            
        return {
            "concepts": context.concepts,
            "notes": _get_result(notes_res, "notes", {}),
            "quiz": _get_result(quiz_res, "quiz", {}),
            "flashcards": _get_result(flashcard_res, "flashcards", {}),
            "mindmap": _get_result(mindmap_res, "mindmap", {})
        }
