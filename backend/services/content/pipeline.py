import asyncio
import logging
from typing import Dict, Any, List
from .context import LectureContext
from ..llm.llm_manager import LLMManager

from .notes import NotesService
from .concept import ConceptService
from .quiz import QuizService
from .flashcard import FlashcardService
from .mindmap import MindmapService
from .interview import InterviewService
from .revision import RevisionService

# CRITICAL-006 / HIGH-001: FormulaService is intentionally NOT imported here.
# It previously ran in Level-1 but its result was discarded (hardcoded {} in the
# return dict). The orchestrator (STEP 8) calls FormulaService directly and uses
# that output. Running it here too was pure wasted LLM spend. Removed.

logger = logging.getLogger(__name__)

class ContentPipeline:
    """
    Orchestrates the execution of domain-specific content services.
    Uses asyncio.gather() to run independent generations concurrently.

    CRITICAL-006 fix: All service results are now captured and returned.
    HIGH-001 fix: Removed redundant formula/interview/revision calls from
    this pipeline (those are already run by orchestrator STEP 8, whose results
    are actually used). Only the unique work this pipeline contributes is kept:
    notes, concepts, quiz, flashcards, and mindmap.
    """
    def __init__(self, llm_manager: LLMManager):
        self.llm_manager = llm_manager
        self.notes_service = NotesService(llm_manager)
        self.concept_service = ConceptService(llm_manager)
        self.quiz_service = QuizService(llm_manager)
        self.flashcard_service = FlashcardService(llm_manager)
        self.mindmap_service = MindmapService(llm_manager)

    async def generate_full_content(self, transcript: str, metadata: Dict[str, Any] = None, segments: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes the full pipeline using a dependency graph and retry logic.
        Returns actual LLM-generated results for all service types.
        """
        logger.info("Starting DAG-based content pipeline...")
        from schemas.content import LectureInput
        lecture_input = LectureInput(transcript=transcript, metadata=metadata or {}, segments=segments or [])
        context = LectureContext(input=lecture_input)
        from schemas.content import ServiceStatus

        # Level 1: Independent prerequisites — run concurrently
        notes_result, concept_result = await asyncio.gather(
            self.notes_service.execute_with_retry("notes", context, self.notes_service.generate_notes, context),
            self.concept_service.execute_with_retry("concept", context, self.concept_service.extract_concepts, context),
        )

        # Level 2: Services that depend on concept extraction
        quiz_result = None
        flashcard_result = None
        mindmap_result = None

        if context.status.get("concept") == ServiceStatus.COMPLETED:
            level_2_coros = [
                self.flashcard_service.execute_with_retry("flashcard", context, self.flashcard_service.generate_flashcards, context),
                self.mindmap_service.execute_with_retry("mindmap", context, self.mindmap_service.generate_mindmap, context),
            ]

            # Quiz additionally depends on notes being available
            if context.status.get("notes") == ServiceStatus.COMPLETED:
                level_2_coros.append(
                    self.quiz_service.execute_with_retry("quiz", context, self.quiz_service.generate_quiz, context)
                )

            level_2_results = await asyncio.gather(*level_2_coros)
            flashcard_result = level_2_results[0]
            mindmap_result = level_2_results[1]
            if len(level_2_results) > 2:
                quiz_result = level_2_results[2]
        else:
            logger.warning("Skipping Level 2 tasks because concept extraction failed.")

        return {
            "concepts": context.concepts,
            "notes": context.topics,
            # CRITICAL-006: Return actual service results, not hardcoded {}
            "quiz": quiz_result or {},
            "flashcards": flashcard_result or {},
            "mindmap": mindmap_result or {},
            # formula/interview/revision are handled exclusively by orchestrator STEP 8
            # to avoid running them twice (HIGH-001). Set to sentinel so callers know.
            "formula": None,
            "interview": None,
            "revision": None,
            "status": {k: v.value for k, v in context.status.items()},
            "errors": context.errors,
        }
