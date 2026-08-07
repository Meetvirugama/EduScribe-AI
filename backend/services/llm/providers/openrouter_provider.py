"""
openrouter_provider.py — OpenRouter Provider

Provides unified access to multiple open-source models including
DeepSeek V3, DeepSeek R1, Qwen3 235B, Llama 3.3 70B, and Qwen3 Coder
— all available on OpenRouter's free tier.

DeepSeek V3 (openrouter/:free) is the PRIMARY model for:
    - Programming explanations (§18.2 PROGRAMMING_EXPLAIN)
    - Code generation (§18.2 CODE_GENERATION)
    - Markdown formatting (secondary)
    - Detailed notes (secondary fallback)

LLD Reference: §15.2 Integrated Provider Reference — Tier 1 / Tier 3
               §18.10.1 DeepSeek V3 Model Profile
               §18.10.2 DeepSeek R1 Model Profile

Free tier limits (§15.2):
    RPM: 20
    RPD: 50/day free; 1,000/day after $10 lifetime purchase (strongly recommended)
    Context: Model-dependent (up to 128K for most models)
    Latency: Medium
"""

import logging
from typing import Any

import litellm

from ..base_provider import BaseProvider, ProviderTransientError, ProviderPermanentError

logger = logging.getLogger(__name__)


class OpenRouterProvider(BaseProvider):
    """
    OpenRouter provider — unified access to DeepSeek, Qwen, Llama, Mistral.

    OpenRouter aggregates dozens of open-source models behind a single API
    endpoint. EduScribe AI uses it primarily for DeepSeek V3 (code, Markdown)
    and Qwen3 235B (mathematics, structured notes).

    LLD Reference: §15.2 Integrated Provider Reference (Tier 1 / Tier 3)
    """

    AVAILABLE_MODELS: list[str] = [
        # Tier 1 — primary open-source models
        "openrouter/deepseek/deepseek-chat:free",         # DeepSeek V3
        "openrouter/deepseek/deepseek-r1:free",           # DeepSeek R1
        "openrouter/qwen/qwen3-235b-a22b:free",           # Qwen3 235B
        "openrouter/meta-llama/llama-3.3-70b-instruct:free",  # Llama 3.3 70B
        "openrouter/qwen/qwen3-coder-480b-a35b:free",    # Qwen3 Coder 480B
    ]

    def __init__(self) -> None:
        super().__init__(provider_name="openrouter")

    async def generate(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Send a chat-completion request via OpenRouter using LiteLLM.

        LLD Note (§18.10.1 DeepSeek V3 Engineering Notes):
            - Preferred chunk size: 800 tokens
            - Ideal context usage: 20K–40K tokens
            - Recommended output budget: 4K–8K tokens
            - Best temperature: 0.2–0.5 for educational content

        Raises:
            ProviderTransientError: Rate limit, timeout, service unavailable.
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
            raise ProviderTransientError(f"OpenRouter rate limit: {exc}") from exc
        except litellm.Timeout as exc:
            raise ProviderTransientError(f"OpenRouter timeout: {exc}") from exc
        except litellm.ServiceUnavailableError as exc:
            raise ProviderTransientError(f"OpenRouter service unavailable: {exc}") from exc
        except litellm.AuthenticationError as exc:
            raise ProviderPermanentError(f"OpenRouter authentication failed: {exc}") from exc
        except litellm.BadRequestError as exc:
            raise ProviderPermanentError(f"OpenRouter bad request: {exc}") from exc

    def get_available_models(self) -> list[str]:
        return self.AVAILABLE_MODELS
