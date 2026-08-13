"""
services/content/flashcard.py — Phase 4 Artifact: Flashcard Generator

Reads ONLY from context.detailed_notes_md (the Phase 3 Detailed Learning Note).
Never reads from the raw transcript.
"""
import logging
from typing import Any, Dict
from .base import BaseContentService
from .context import LectureContext
from ..llm.model_selector import TaskType

logger = logging.getLogger(__name__)


class FlashcardGenerator(BaseContentService):
    async def generate_flashcards(
            self, context: LectureContext) -> Dict[str, Any]:
        """Generates spaced repetition flashcards from the Detailed Learning Note."""
        logger.info("Generating flashcards from Detailed Learning Note...")

        empty_result = {"topic": "", "flashcards": []}

        if not self.llm_manager:
            return empty_result

        learning_note = context.detailed_notes_md
        if not learning_note.strip():
            logger.warning(
                "FlashcardGenerator: detailed_notes_md is empty. Falling back to transcript.")
            learning_note = context.transcript

        messages = self._render_messages(
            system_msg="You are an expert at creating concise, effective flashcards. Output only valid JSON.",
            template_name="flashcards",
            learning_note=learning_note
        )

        try:
            response = await self.llm_manager.generate(TaskType.FLASHCARD_GENERATION, messages)
            return self._safe_dump(response, fallback=empty_result)
        except Exception as exc:
            logger.error("FlashcardGenerator: generation failed: %s", exc)
            return empty_result
