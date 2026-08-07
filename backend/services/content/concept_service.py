from .base_service import BaseContentService
from .lecture_context import LectureContext
from ..llm.model_selector import TaskType
import logging

logger = logging.getLogger(__name__)

class ConceptService(BaseContentService):
    async def extract_concepts(self, context: LectureContext) -> dict:
        """Extracts key academic concepts, technical terms, and important keywords."""
        logger.info("Extracting concepts and keywords...")
        messages = self._render_messages(
            system_msg="You are an expert AI tutor that strictly outputs valid JSON.",
            template_name="concept_extraction",
            context=context
        )
        
        response = await self.llm_manager.generate(TaskType.CONCEPT_EXTRACTION, messages)
        result = self._safe_dump(response, fallback={"concepts": [], "keywords": [], "key_phrases": []})
        
        # Save to context for reuse by downstream services
        context.concepts = result.get("concepts", [])
        return result
