from .base import BaseContentService
from .context import LectureContext
from ..llm.model_selector import TaskType
import logging

logger = logging.getLogger(__name__)

class NotesService(BaseContentService):
    async def generate_notes(self, context: LectureContext) -> dict:
        """Generates detailed, structured notes from the transcript."""
        logger.info("Generating detailed notes...")
        messages = self._render_messages(
            system_msg="You are an expert AI tutor that strictly outputs valid JSON.",
            template_name="detailed_notes",
            context=context
        )
        
        response = await self.llm_manager.generate(TaskType.DETAILED_NOTES, messages)
        return self._safe_dump(response, fallback={"summary": "Failed to generate notes.", "topics": []})
