from .base import BaseContentService
from .context import LectureContext
from ..llm.model_selector import TaskType
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

class RevisionService(BaseContentService):
    """Generates condensed revision sheets for exam preparation."""

    async def generate_revision_sheet(self, context: LectureContext) -> Dict[str, Any]:
        """Generate a concise revision sheet."""
        logger.info("Generating revision sheet...")
        
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
            
        # Build transcript context
        transcript_text = " ".join(s.get("text", "") for s in context.segments)
        if not transcript_text.strip():
            transcript_text = getattr(context.input, "transcript", "")
            if not transcript_text.strip():
                logger.warning("No transcript provided for revision sheet generation.")
                transcript_text = "No transcript provided."

        # Build topics context
        topics = context.topics[:5] if context.topics else []
        topics_context = ", ".join(t.get("title", "") for t in topics)

        # Build concepts context
        concepts = context.concepts[:8] if context.concepts else []
        concepts_context = ", ".join(getattr(c, "name", str(c)) for c in concepts if getattr(c, "importance", "") == "high")

        messages = self._render_messages(
            system_msg="You are an exam revision expert. Output only valid JSON.",
            template_name="revision",
            topics_context=topics_context or "See transcript",
            concepts_context=concepts_context or "See transcript",
            transcript_text=transcript_text
        )
        
        try:
            response = await self.llm_manager.generate(TaskType.REVISION_GENERATION, messages)
            
            raw_dict = self._safe_dump(response, fallback=empty_result)
            
            from ..llm.validation.schemas.notes import RevisionSheetOutput
            parsed = RevisionSheetOutput(**raw_dict)
            
            return parsed.model_dump()
            
        except Exception as exc:
            logger.error("RevisionService: generation failed: %s", exc)
            return empty_result
