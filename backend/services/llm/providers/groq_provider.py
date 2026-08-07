"""
groq_provider.py — Groq Provider (Tier 2 — High-Speed Free)

Groq provides very fast inference (14,400 RPD) with sub-second latency.
Used as primary for Markdown formatting and JSON extraction tasks,
and as emergency fallback for most other tasks.

LLD Reference: §15.2 Integrated Provider Reference — Tier 2
               §18.2 Routing Table — primary for MARKDOWN_FORMAT,
                                     emergency for most other tasks

Available models (§15.2):
    groq/llama-3.3-70b-versatile           — Main 70B model (14,400 RPD)
    groq/qwen3-32b                          — Qwen3 32B on Groq
    groq/llama-3.1-8b-instant              — Emergency / Tier 4 (fastest)
    groq/deepseek-r1-distill-llama-70b     — Emergency for math tasks

Free tier limits (§15.2):
    RPM: 30
    RPD: 14,400
    Context: 128K tokens
    Latency: Very fast
"""

import logging
from typing import Any

import litellm

from ..base_provider import BaseProvider, ProviderTransientError, ProviderPermanentError

logger = logging.getLogger(__name__)


class GroqProvider(BaseProvider):
    """
    Groq provider — Tier 2 high-speed inference.

    The highest RPD provider (14,400/day), making it ideal for
    formatting-only tasks (Markdown, JSON extraction) that require
    no deep reasoning but benefit from high throughput.

    LLD Reference: §15.2 Integrated Provider Reference (Tier 2)
                   §18.2 Routing Table — MARKDOWN_FORMAT primary
    """

    AVAILABLE_MODELS: list[str] = [
        "groq/llama-3.3-70b-versatile",
        "groq/qwen3-32b",
        "groq/llama-3.1-8b-instant",
        "groq/deepseek-r1-distill-llama-70b",
    ]

    def __init__(self) -> None:
        super().__init__(provider_name="groq")

    async def generate(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Send a chat-completion request to Groq via LiteLLM.

        LLD Note (§18.2): Groq handles Markdown formatting and JSON extraction
        tasks — 14,400 RPD means quota rarely runs out, preserving Gemini's
        more limited quota for deep content generation.

        Raises:
            ProviderTransientError: Rate limit, timeout.
            ProviderPermanentError: Authentication failure, bad request.
        """
        api_key = kwargs.pop("api_key", None)

        try:
            response = await litellm.acompletion(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=api_key,
                num_retries=0,
                **kwargs,
            )
            return response

        except litellm.RateLimitError as exc:
            raise ProviderTransientError(f"Groq rate limit: {exc}") from exc
        except litellm.Timeout as exc:
            raise ProviderTransientError(f"Groq timeout: {exc}") from exc
        except litellm.ServiceUnavailableError as exc:
            raise ProviderTransientError(f"Groq service unavailable: {exc}") from exc
        except litellm.AuthenticationError as exc:
            raise ProviderPermanentError(f"Groq authentication failed: {exc}") from exc
        except litellm.BadRequestError as exc:
            raise ProviderPermanentError(f"Groq bad request: {exc}") from exc

    def get_available_models(self) -> list[str]:
        return self.AVAILABLE_MODELS
