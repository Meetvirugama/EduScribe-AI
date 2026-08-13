"""
services/content/mindmap.py — Phase 4 Artifact: Mind Map Generator

Reads ONLY from context.detailed_notes_md (the Phase 3 Detailed Learning Note).
Never reads from the raw transcript.
"""
import logging
from typing import Any, Dict
from .base import BaseContentService
from .context import LectureContext
from ..llm.model_selector import TaskType

logger = logging.getLogger(__name__)


class MindmapGenerator(BaseContentService):
    async def generate_mindmap(
            self, context: LectureContext) -> Dict[str, Any]:
        """Generates a Mermaid.js mind map from the Detailed Learning Note."""
        logger.info("Generating mindmap from Detailed Learning Note...")

        empty_result = {"topic": "", "format": "mermaid", "content": ""}

        if not self.llm_manager:
            return empty_result

        learning_note = context.detailed_notes_md
        if not learning_note.strip():
            logger.warning(
                "MindmapGenerator: detailed_notes_md is empty. Falling back to transcript.")
            learning_note = context.transcript

        messages = self._render_messages(
            system_msg="You are an expert AI tutor. Output only valid JSON.",
            template_name="mindmap",
            learning_note=learning_note
        )

        try:
            response = await self.llm_manager.generate(TaskType.MIND_MAP_GENERATION, messages)
            raw_dict = self._safe_dump(response, fallback=empty_result)
            from ..llm.validation.schemas.core import MindMap
            parsed = MindMap(**raw_dict)
            return parsed.model_dump()
        except Exception as exc:
            logger.error("MindmapGenerator: generation failed: %s", exc)
            return empty_result
