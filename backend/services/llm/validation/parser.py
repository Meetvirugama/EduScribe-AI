import logging
from typing import Any
from .exceptions import ResponseParseError

logger = logging.getLogger(__name__)

class RawResponseParser:
    """
    Normalises raw LiteLLM API responses into a consistent internal dictionary format.
    Extracts text content, usage statistics, and model metadata.
    """
    @staticmethod
    def parse(raw_response: Any, provider: str = "unknown") -> dict[str, Any]:
        if raw_response is None:
            raise ResponseParseError("LiteLLM returned None — provider may have errored.")

        try:
            choice = raw_response.choices[0]
            content: str = choice.message.content or ""

            usage_obj = getattr(raw_response, "usage", None)
            usage = {
                "prompt_tokens":     getattr(usage_obj, "prompt_tokens", 0) or 0,
                "completion_tokens": getattr(usage_obj, "completion_tokens", 0) or 0,
                "total_tokens":      getattr(usage_obj, "total_tokens", 0) or 0,
            }

            return {
                "content":       content,
                "model":         getattr(raw_response, "model", "unknown"),
                "provider":      provider,
                "usage":         usage,
                "finish_reason": getattr(choice, "finish_reason", "unknown"),
                "raw":           raw_response,
            }

        except (AttributeError, IndexError, TypeError) as exc:
            logger.error(f"failed to parse response from '{provider}': {exc}\nRaw: {raw_response}")
            raise ResponseParseError(f"Could not parse LiteLLM response from '{provider}': {exc}") from exc

    @staticmethod
    def is_truncated(parsed: dict[str, Any]) -> bool:
        return parsed.get("finish_reason") == "length"
