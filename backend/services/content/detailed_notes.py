import logging
from typing import Dict, Any

from .base import BaseContentService
from .context import LectureContext
from ..llm.model_selector import TaskType

logger = logging.getLogger(__name__)

class DetailedNotesGenerator(BaseContentService):
    async def generate_detailed_notes(self, context: LectureContext) -> Dict[str, Any]:
        """Generates detailed, structured notes using extracted topics."""
        logger.info("Generating detailed notes artifact...")
        
        empty_result = {"notes_markdown": "Failed to generate notes."}
        
        if not self.llm_manager:
            return empty_result
            
        topics_context = ""
        for topic in context.topics:
            topics_context += f"- {topic.get('title', 'Unknown')}\n"
                
        if not topics_context:
            logger.warning("No topics available for detailed notes generation.")
            topics_context = "No topics provided."
            
        messages = self._render_messages(
            system_msg="You are an expert educational notes creator.",
            template_name="detailed_notes_artifact",
            topics_context=topics_context,
            transcript_text=context.transcript
        )
        
        try:
            # Re-using detailed notes task type
            response = await self.llm_manager.generate(TaskType.DETAILED_NOTES, messages)
            
            raw_dict = self._safe_dump(response, fallback=empty_result)
            return raw_dict
            
        except Exception as exc:
            logger.error("DetailedNotesGenerator: generation failed: %s", exc)
            return empty_result
