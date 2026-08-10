from .base import BaseContentService
from .context import LectureContext
from ..llm.model_selector import TaskType
import logging

logger = logging.getLogger(__name__)

class FlashcardGenerator(BaseContentService):
    async def generate_flashcards(self, context: LectureContext) -> dict:
        """Generates spaced repetition flashcards."""
        logger.info("Generating flashcards...")
        messages = self._render_messages(
            system_msg="You are an expert at creating concise, effective flashcards.",
            template_name="flashcards",
            context=context
        )
        
        response = await self.llm_manager.generate(TaskType.FLASHCARD_GENERATION, messages)
        return self._safe_dump(response, fallback={"topic": "", "flashcards": []})
