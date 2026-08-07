"""
google_provider.py — Google AI Studio Provider (Gemini 2.5 Flash / Flash Lite)

Implements the Google AI Studio integration using LiteLLM.
Gemini 2.5 Flash is the PRIMARY provider for most EduScribe AI tasks due to:
  - 1M token context window (largest among all integrated providers)
  - Multimodal capabilities (text, image, audio, video, PDF)
  - Excellent educational content generation scores (9.9/10)
  - Generous free tier (no credit card required)

LLD Reference: §15.2 Integrated Provider Reference — Tier 1 (Primary)
               §18.10.3 Gemini 2.5 Flash Model Profile

Available models (LLD §15.2):
    gemini/gemini-2.5-flash              — Tier 1 primary
    gemini/gemini-2.5-flash-lite-preview-06-17 — Tier 1 secondary / Markdown formatting

Free tier limits (§15.2):
    RPM: ~15 (verify)
    RPD: ~1,500 (verify)
    Context: 1,048,576 tokens (1M)
    Latency: Medium
"""

import logging
from typing import Any

import litellm

from ..base_provider import BaseProvider, ProviderTransientError, ProviderPermanentError

logger = logging.getLogger(__name__)


class GoogleProvider(BaseProvider):
    """
    Google AI Studio provider — Gemini 2.5 Flash and Flash Lite.

    The PRIMARY provider for EduScribe AI. Selected for its 1M token
    context window, multimodal support (OCR, video-to-notes), and strong
    educational content generation capability.

    All calls go through LiteLLM so no google-generativeai SDK is imported
    directly — provider abstraction is maintained at all times (§24.2).

    LLD Reference: §15.2 Integrated Provider Reference (Tier 1)
                   §18.10.3 Gemini 2.5 Flash Model Profile
    """

    AVAILABLE_MODELS: list[str] = [
        "gemini/gemini-2.5-flash",
        "gemini/gemini-2.5-flash-lite-preview-06-17",
    ]

    # Production configuration from LLD §18.10.3
    DEFAULT_TEMPERATURE: float = 0.3
    DEFAULT_TOP_P: float = 0.9
    DEFAULT_TOP_K: int = 40

    def __init__(self) -> None:
        super().__init__(provider_name="google")

    async def generate(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Send a chat-completion request to Google AI Studio via LiteLLM.

        LLD Note (§18.10.3 Engineering Considerations):
            - Ideal context window usage: 100K–300K tokens
            - Ideal output: 4K–12K tokens
            - Temperature: 0.3 (educational content), 0.1 (structured extraction)
            - Streaming: enabled
            - Vision / Function Calling / JSON Mode: enabled

        Args:
            model:       LiteLLM model ID, e.g. "gemini/gemini-2.5-flash".
            messages:    OpenAI-format message list.
            temperature: Sampling temperature (§18.10.3: 0.3 for most tasks).
            max_tokens:  Maximum completion tokens.
            **kwargs:    Additional parameters forwarded to LiteLLM.

        Returns:
            Raw LiteLLM response object (parsed by ResponseParser in llm_manager).

        Raises:
            ProviderTransientError: Rate limit (429), timeout, service unavailable.
            ProviderPermanentError: Authentication failure (401/403), bad request.
        """
        api_key = kwargs.pop("api_key", None)

        try:
            logger.debug(
                "google_provider: calling model=%s messages=%d tokens=%d",
                model,
                len(messages),
                max_tokens,
            )
            response = await litellm.acompletion(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=self.DEFAULT_TOP_P,
                api_key=api_key,
                num_retries=0,      # retries handled by retry_manager
                **kwargs,
            )
            logger.debug(
                "google_provider: success model=%s tokens=%s",
                model,
                getattr(getattr(response, "usage", None), "total_tokens", "?"),
            )
            return response

        except litellm.RateLimitError as exc:
            raise ProviderTransientError(f"Google rate limit: {exc}") from exc
        except litellm.Timeout as exc:
            raise ProviderTransientError(f"Google timeout: {exc}") from exc
        except litellm.ServiceUnavailableError as exc:
            raise ProviderTransientError(f"Google service unavailable: {exc}") from exc
        except litellm.AuthenticationError as exc:
            raise ProviderPermanentError(f"Google authentication failed: {exc}") from exc
        except litellm.BadRequestError as exc:
            raise ProviderPermanentError(f"Google bad request: {exc}") from exc

    def get_available_models(self) -> list[str]:
        return self.AVAILABLE_MODELS
