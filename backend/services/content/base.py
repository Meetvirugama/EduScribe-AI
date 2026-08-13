import logging
from typing import Any, Dict, List
from .context import LectureContext
from ..llm.llm_manager import LLMManager
from .prompts import PromptManager
from ..llm.validation.schemas.core import GenericTextOutput

logger = logging.getLogger(__name__)


class BaseContentService:
    def __init__(self, llm_manager: LLMManager):
        self.llm_manager = llm_manager

    def _render_messages(self, system_msg: str,
                         template_name: str, **kwargs) -> List[Dict[str, str]]:
        """Renders the user prompt from a template and wraps it in a standard message structure."""
        prompt = PromptManager.render(template_name, **kwargs)
        return [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt}
        ]

    def _safe_dump(self, response: Any,
                   fallback: Dict[str, Any]) -> Dict[str, Any]:
        """Safely dumps a Pydantic response or extracts JSON if it's GenericTextOutput."""
        try:
            if isinstance(response, GenericTextOutput):
                from ..llm.validation.json_utils import JSONExtractor
                return JSONExtractor.extract_and_repair(response.text)
            return response.model_dump()
        except Exception as e:
            logger.error(f"Failed to dump response: {e}")
            return fallback

    async def execute_with_retry(
            self, service_name: str, context: LectureContext, func, *args, **kwargs):
        """Executes a content service function with retry logic and status tracking."""
        from schemas.content import ServiceStatus
        import asyncio

        max_retries = 2
        context.status[service_name] = ServiceStatus.RUNNING

        for attempt in range(max_retries):
            try:
                result = await func(*args, **kwargs)
                context.status[service_name] = ServiceStatus.COMPLETED
                return result
            except Exception as e:
                logger.warning(
                    f"Attempt {attempt + 1} failed for {service_name}: {e}")
                if attempt == max_retries - 1:
                    context.status[service_name] = ServiceStatus.FAILED
                    context.errors[service_name] = str(e)
                    logger.error(
                        f"Service {service_name} completely failed after {max_retries} attempts.")
                    return None
                await asyncio.sleep(2 ** attempt)
