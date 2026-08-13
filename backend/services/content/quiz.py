"""
services/content/quiz.py — Phase 4 Artifact: Quiz Generator

Reads ONLY from context.detailed_notes_md (the Phase 3 Detailed Learning Note).
Never reads from the raw transcript.
"""
import logging
from typing import Any, Dict
from .base import BaseContentService
from .context import LectureContext
from ..llm.model_selector import TaskType

logger = logging.getLogger(__name__)

class QuizGenerator(BaseContentService):
    async def generate_quiz(self, context: LectureContext) -> Dict[str, Any]:
        """Generates quiz questions from the Detailed Learning Note."""
        logger.info("Generating quiz from Detailed Learning Note...")
        
        empty_result = {"topic": "", "subtopic": "", "questions": []}
        
        if not self.llm_manager:
            return empty_result
        
        learning_note = context.detailed_notes_md
        if not learning_note.strip():
            logger.warning("QuizGenerator: detailed_notes_md is empty. Falling back to transcript.")
            learning_note = context.transcript
        
        diff_level = getattr(context.input, "difficulty", 3)
        
        messages = self._render_messages(
            system_msg="You are an expert AI tutor and assessment designer. Output only valid JSON.",
            template_name="quiz",
            learning_note=learning_note,
            difficulty=diff_level
        )
        
        try:
            response = await self.llm_manager.generate(TaskType.QUIZ_GENERATION, messages)
            return self._safe_dump(response, fallback=empty_result)
        except Exception as exc:
            logger.error("QuizGenerator: generation failed: %s", exc)
            return empty_result
