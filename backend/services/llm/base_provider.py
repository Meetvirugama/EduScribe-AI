"""
base_provider.py — Abstract BaseProvider Interface

Every LLM provider integration in EduScribe AI must inherit from this class.
No component outside the services/llm/ directory ever calls an LLM directly;
all calls flow through: LLM Manager → model_selector → key_manager → LiteLLM → provider API.

LLD Reference: §15.3 Folder Structure, §15 LLM Provider Architecture
"""

from abc import ABC, abstractmethod
from typing import Any




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
