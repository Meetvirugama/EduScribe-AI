from .base import BaseContentService
from .context import LectureContext
from ..llm.model_selector import TaskType
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

class MindmapGenerator(BaseContentService):
    async def generate_mindmap(self, context: LectureContext) -> dict:
        """Generates Mermaid.js mind map code."""
        logger.info("Generating mind map...")
        messages = self._render_messages(
            system_msg="You are an expert at creating Mermaid.js diagrams.",
            template_name="mindmap",
            context=context
        )
        
        empty_result = {"topic": "", "format": "mermaid", "content": ""}
        
        if not self.llm_manager:
            return empty_result
            
        # Build transcript context
        transcript_text = " ".join(s.get("text", "") for s in context.segments)
        if not transcript_text.strip():
            transcript_text = getattr(context.input, "transcript", "")
            if not transcript_text.strip():
                logger.warning("No transcript provided for mindmap generation.")
                transcript_text = "No transcript provided."

        # Build concepts context
        concepts = context.concepts[:15] if context.concepts else []
        concepts_context = ", ".join(getattr(c, "name", str(c)) for c in concepts)
        
        messages = self._render_messages(
            system_msg="You are an expert AI tutor.",
            template_name="mindmap",
            transcript_text=transcript_text,
            concepts_context=concepts_context or "See transcript"
        )
        
        try:
            response = await self.llm_manager.generate(TaskType.MIND_MAP_GENERATION, messages)
            
            raw_dict = self._safe_dump(response, fallback=empty_result)
            
            from ..llm.validation.schemas.core import MindMap
            parsed = MindMap(**raw_dict)
            
            return parsed.model_dump()
            
        except Exception as exc:
            logger.error("MindmapService: generation failed: %s", exc)
            return empty_result
