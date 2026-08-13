"""
services/content/revision.py — Phase 4 Artifact: Revision Sheet Generator

Reads ONLY from context.detailed_notes_md (the Phase 3 Detailed Learning Note).
Never reads from the raw transcript.
"""
import logging
from typing import Any, Dict
from .base import BaseContentService
from .context import LectureContext
from ..llm.model_selector import TaskType

logger = logging.getLogger(__name__)

class RevisionGenerator(BaseContentService):
    """Generates condensed revision sheets for exam preparation."""

    async def generate_revision_sheet(self, context: LectureContext) -> Dict[str, Any]:
        """Generate a concise revision sheet from the Detailed Learning Note."""
        logger.info("Generating revision sheet from Detailed Learning Note...")
        
        empty_result = {
            "title": "Revision Sheet",
            "quick_facts": [],
            "key_definitions": [],
            "important_formulas": [],
            "must_know_points": [],
            "priority_topics": [],
            "last_minute_tips": []
        }
        
        if not self.llm_manager:
            return empty_result
        
        learning_note = context.detailed_notes_md
        if not learning_note.strip():
            logger.warning("RevisionGenerator: detailed_notes_md is empty. Falling back to transcript.")
            learning_note = context.transcript
        
        messages = self._render_messages(
            system_msg="You are an exam revision expert. Output only valid JSON.",
            template_name="revision",
            learning_note=learning_note
        )
        
        try:
            response = await self.llm_manager.generate(TaskType.REVISION_GENERATION, messages)
            raw_dict = self._safe_dump(response, fallback=empty_result)
            from ..llm.validation.schemas.notes import RevisionSheetOutput
            parsed = RevisionSheetOutput(**raw_dict)
            return parsed.model_dump()
        except Exception as exc:
            logger.error("RevisionGenerator: generation failed: %s", exc)
            return empty_result
