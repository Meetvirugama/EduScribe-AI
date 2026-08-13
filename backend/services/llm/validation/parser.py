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
    def parse(
        raw_response: Any,
        provider: str = "unknown",
    ) -> dict[str, Any]:

        if raw_response is None:
            raise ResponseParseError(
                "LiteLLM returned None — provider may have errored.")

        try:
            choices = getattr(raw_response, "choices", None)
            if not choices:
                raise ResponseParseError(
                    "LiteLLM response contained no choices.")

            choice = choices[0]

            # Explicitly check for None content (e.g. content_filter triggers)
            content_value = getattr(
                getattr(
                    choice,
                    "message",
                    None),
                "content",
                None)
            if content_value is None:
                raise ResponseParseError(
                    "LiteLLM returned None content (possible content_filter or provider failure).")
            content: str = content_value

            usage_obj = getattr(raw_response, "usage", None)

            # Robust extraction handling both object and dictionary usage
            # formats
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0

            if usage_obj is not None:
                if isinstance(usage_obj, dict):
                    prompt_tokens = usage_obj.get("prompt_tokens", 0) or 0
                    completion_tokens = usage_obj.get(
                        "completion_tokens", 0) or 0
                    total_tokens = usage_obj.get("total_tokens", 0) or 0
                else:
                    prompt_tokens = getattr(usage_obj, "prompt_tokens", 0) or 0
                    completion_tokens = getattr(
                        usage_obj, "completion_tokens", 0) or 0
                    total_tokens = getattr(usage_obj, "total_tokens", 0) or 0

            usage = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
            }

            return {
                "content": content,
                "model": getattr(raw_response, "model", "unknown"),
                "provider": provider,
                "usage": usage,
                "finish_reason": getattr(
                    choice,
                    "finish_reason",
                    "unknown",
                ),
                "raw": raw_response,
            }

        except (AttributeError, IndexError, TypeError) as exc:
            # Privacy safe error logging (does NOT dump raw_response)
            logger.error(f"failed to parse response from '{provider}': {exc}")
            raise ResponseParseError(
                f"Could not parse LiteLLM response from '{provider}': {exc}"
            ) from exc

    @staticmethod
    def is_truncated(parsed: dict[str, Any]) -> bool:
        return parsed.get("finish_reason") == "length"
