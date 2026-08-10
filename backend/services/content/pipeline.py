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
from .formula import FormulaService
from .interview import InterviewService
from .revision import RevisionService

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
        self.formula_service = FormulaService(llm_manager)
        self.interview_service = InterviewService(llm_manager)
        self.revision_service = RevisionService(llm_manager)

    async def generate_full_content(self, transcript: str, metadata: Dict[str, Any] = None, segments: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes the full pipeline using a dependency graph and retry logic.
        """
        logger.info("Starting DAG-based content pipeline...")
        from schemas.content import LectureInput
        lecture_input = LectureInput(transcript=transcript, metadata=metadata or {}, segments=segments or [])
        context = LectureContext(input=lecture_input)
        from schemas.content import ServiceStatus
        
        # Level 1: Independent prerequisites
        await asyncio.gather(
            self.concept_service.execute_with_retry("concept", context, self.concept_service.extract_concepts, context),
            self.notes_service.execute_with_retry("notes", context, self.notes_service.generate_notes, context),
            self.formula_service.execute_with_retry("formula", context, self.formula_service.generate_formula_sheet, context),
        )
        
        # Level 2: Dependent services
        level_2_tasks = []
        
        # Mindmap, Flashcards, and Interviews depend on concepts
        if context.status.get("concept") == ServiceStatus.COMPLETED:
            level_2_tasks.extend([
                self.flashcard_service.execute_with_retry("flashcard", context, self.flashcard_service.generate_flashcards, context),
                self.mindmap_service.execute_with_retry("mindmap", context, self.mindmap_service.generate_mindmap, context),
                self.interview_service.execute_with_retry("interview", context, self.interview_service.generate_interview_questions, context)
            ])
            
            # Quiz and Revision depend on both concepts and notes
            if context.status.get("notes") == ServiceStatus.COMPLETED:
                level_2_tasks.extend([
                    self.quiz_service.execute_with_retry("quiz", context, self.quiz_service.generate_quiz, context),
                    self.revision_service.execute_with_retry("revision", context, self.revision_service.generate_revision_sheet, context)
                ])
        else:
            logger.warning("Skipping Level 2 tasks because concept extraction failed.")
            
        if level_2_tasks:
            await asyncio.gather(*level_2_tasks)
            
        return {
            "concepts": context.concepts,
            "notes": context.topics, # Assume notes populate topics or similar
            "quiz": {}, # Ideally fetch from context or return values
            "flashcards": {},
            "mindmap": {},
            "formula": {},
            "interview": {},
            "revision": {},
            "status": {k: v.value for k, v in context.status.items()},
            "errors": context.errors
        }
