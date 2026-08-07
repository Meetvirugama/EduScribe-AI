from .base_service import BaseContentService
from .lecture_context import LectureContext
from ..llm.model_selector import TaskType
import logging

logger = logging.getLogger(__name__)

class FlashcardService(BaseContentService):
    async def generate_flashcards(self, context: LectureContext) -> dict:
        """Generates flashcards for key terms and definitions."""
        logger.info("Generating flashcards...")
        messages = self._render_messages(
            system_msg="You are an expert AI tutor.",
            template_name="flashcards",
            context=context
        )
        
        response = await self.llm_manager.generate(TaskType.FLASHCARD_GENERATION, messages)
        return self._safe_dump(response, fallback={"topic": "", "flashcards": []})
