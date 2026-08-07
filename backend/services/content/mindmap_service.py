from .base_service import BaseContentService
from .lecture_context import LectureContext
from ..llm.model_selector import TaskType
import logging

logger = logging.getLogger(__name__)

class MindmapService(BaseContentService):
    async def generate_mindmap(self, context: LectureContext) -> dict:
        """Generates a mermaid.js mindmap of the lecture."""
        logger.info("Generating mind map...")
        messages = self._render_messages(
            system_msg="You are an expert AI tutor.",
            template_name="mindmap",
            context=context
        )
        
        response = await self.llm_manager.generate(TaskType.MIND_MAP_GENERATION, messages)
        return self._safe_dump(response, fallback={"topic": "", "format": "mermaid", "content": ""})
