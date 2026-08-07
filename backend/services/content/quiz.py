from .base import BaseContentService
from .context import LectureContext
from ..llm.model_selector import TaskType
import logging

logger = logging.getLogger(__name__)

class QuizService(BaseContentService):
    async def generate_quiz(self, context: LectureContext) -> dict:
        """Generates challenging quiz questions based on the transcript and context."""
        logger.info("Generating quiz questions...")
        messages = self._render_messages(
            system_msg="You are an expert AI tutor and assessment designer.",
            template_name="quiz",
            context=context
        )
        
        response = await self.llm_manager.generate(TaskType.QUIZ_GENERATION, messages)
        return self._safe_dump(response, fallback={"topic": "", "subtopic": "", "questions": []})
