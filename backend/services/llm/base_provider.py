"""
base_provider.py — Abstract BaseProvider Interface

Every LLM provider integration in EduScribe AI must inherit from this class.
No component outside the services/llm/ directory ever calls an LLM directly;
all calls flow through: LLM Manager → model_selector → key_manager → LiteLLM → provider API.

LLD Reference: §15.3 Folder Structure, §15 LLM Provider Architecture
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseProvider(ABC):
    """
    Abstract base class for all LLM provider implementations.

    Each concrete subclass corresponds to one integrated LLM provider
    (Google AI Studio, OpenRouter, Cerebras, Groq, Together AI,
    SambaNova, Mistral). Subclasses implement the provider-specific
    details; all routing and resilience logic lives in llm_manager.py,
    fallback_manager.py, key_manager.py, and retry_manager.py.

    Design constraints from LLD §15:
    - Provider abstraction is MANDATORY — the application must NEVER
      call a vendor SDK directly. Every call goes through this layer.
    - A new provider is added by implementing a new subclass here.
    - Removing a provider requires no changes outside services/llm/.
    """

    def __init__(self, provider_name: str):
        """
        Args:
            provider_name: Human-readable name, e.g. "google", "groq".
                           Used for logging and quota tracking.
        """
        self.provider_name = provider_name

    @abstractmethod
    async def generate(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Send a chat-completion request to this provider and return the
        normalised response dictionary.

        All providers expose the same signature so that llm_manager.py
        can call any provider interchangeably without branching logic.

        Args:
            model:       LiteLLM model ID or proxy alias, e.g. "gemini-flash".
            messages:    OpenAI-format message list
                         [{"role": "system", "content": "..."}, ...].
            temperature: Sampling temperature (0.0 = deterministic).
            max_tokens:  Maximum completion tokens.
            **kwargs:    Additional provider-specific options passed
                         through to LiteLLM transparently.

        Returns:
            A dict containing at minimum:
            {
                "content": str,            # the model's text response
                "model": str,              # actual model used
                "usage": {
                    "prompt_tokens": int,
                    "completion_tokens": int,
                    "total_tokens": int,
                },
                "provider": str,           # self.provider_name
            }

        Raises:
            ProviderTransientError: For retryable failures (rate limit,
                                    timeout). The retry_manager will catch this.
            ProviderPermanentError: For permanent failures (invalid API key,
                                    malformed request). No retry attempted.
        """
        ...

    @abstractmethod
    def get_available_models(self) -> list[str]:
        """
        Return the list of LiteLLM model IDs available through this provider.
        Used by model_selector.py and llm_manager.py for routing decisions.
        """
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} provider={self.provider_name!r}>"


class ProviderTransientError(Exception):
    """
    Raised for retryable, temporary provider failures.
    Examples: HTTP 429 rate limit, timeout, HTTP 503 Service Unavailable.

    The retry_manager.py (Tenacity) will catch this and apply exponential backoff:
        Attempt 1 — immediate
        Attempt 2 — wait 2 s
        Attempt 3 — wait 4 s
        Attempt 4 — wait 8 s
        Attempt 5 — escalate to fallback_manager (switch provider)

    LLD Reference: §19 Retry Strategy
    """


class ProviderPermanentError(Exception):
    """
    Raised for non-retryable, permanent provider failures.
    Examples: invalid API key (HTTP 401/403), malformed request (HTTP 400).

    These bypass the retry mechanism entirely and fail immediately,
    since retrying a permanent error can never succeed and would only
    waste quota.

    LLD Reference: §19 Retry Strategy — Transient vs. Permanent Failures
    """
