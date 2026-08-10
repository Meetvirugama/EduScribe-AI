from .base import BaseContentService
from .context import LectureContext
from ..llm.model_selector import TaskType
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

class TopicService(BaseContentService):
    async def extract_topics(self, context: LectureContext) -> Dict[str, Any]:
        """Extracts topics from the transcript."""
        logger.info("Extracting topics...")
        
        empty_result = {"summary": "Failed to extract topics.", "topics": []}
        
        if not self.llm_manager:
            return empty_result
            
        # Build transcript context
        transcript_text = " ".join(s.get("text", "") for s in context.segments)
        if not transcript_text.strip():
            transcript_text = getattr(context.input, "transcript", "")
            if not transcript_text.strip():
                logger.warning("No transcript provided for notes generation.")
                transcript_text = "No transcript provided."
                
        messages = self._render_messages(
            system_msg="You are an expert AI tutor that strictly outputs valid JSON.",
            template_name="topic_extraction",
            transcript_text=transcript_text
        )
        
        try:
            response = await self.llm_manager.generate(TaskType.DETAILED_NOTES, messages)
            
            raw_dict = self._safe_dump(response, fallback=empty_result)
            
            from ..llm.validation.schemas.notes import TopicsAndNotesOutput
            parsed = TopicsAndNotesOutput(**raw_dict)
            
            # Save parsed topics back to context so downstream services can use them
            context.topics = [t.model_dump() for t in parsed.topics]
            
            return parsed.model_dump()
            
        except Exception as exc:
            logger.error("TopicService: extraction failed: %s", exc)
            return empty_result
