import logging
from typing import Any, Dict, List
from .lecture_context import LectureContext
from ..llm.llm_manager import LLMManager
from .prompt_manager import PromptManager
from ..llm.validation.schemas.core import GenericTextOutput

logger = logging.getLogger(__name__)

class BaseContentService:
    def __init__(self, llm_manager: LLMManager):
        self.llm_manager = llm_manager
        
    def _render_messages(self, system_msg: str, template_name: str, context: LectureContext) -> List[Dict[str, str]]:
        """Renders the user prompt from a template and wraps it in a standard message structure."""
        prompt = PromptManager.render(template_name, context=context)
        return [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt}
        ]
        
    def _safe_dump(self, response: Any, fallback: Dict[str, Any]) -> Dict[str, Any]:
        """Safely dumps a Pydantic response or extracts JSON if it's GenericTextOutput."""
        try:
            if isinstance(response, GenericTextOutput):
                from ..llm.validation.json_utils import JSONExtractor
                return JSONExtractor.extract_and_repair(response.text)
            return response.model_dump()
        except Exception as e:
            logger.error(f"Failed to dump response: {e}")
            return fallback
