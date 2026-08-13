"""
retry_manager.py — Intra-Provider Retry with Exponential Backoff

Implements the Retry Strategy described in §19. Transient failures
(timeouts, rate limiting) are retried up to four times with
exponential backoff before the request is escalated to the
Fallback Strategy (switch provider).

Permanent failures (invalid API key, malformed request) bypass
retries entirely and fail immediately.

LLD Reference: §19 Retry Strategy
               §19.3 Detailed Explanation — Exponential Backoff Schedule
               §23 Technology Stack — Tenacity implements retry

Exponential backoff schedule (§19.3):
    Attempt 1 — immediate retry
    Attempt 2 — wait 2 seconds
    Attempt 3 — wait 4 seconds
    Attempt 4 — wait 8 seconds
    Attempt 5 — switch provider (escalate to Fallback Strategy §20)
"""

import logging
from typing import Any, Callable, Awaitable

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    RetryError,
)

from .base_provider import ProviderTransientError, ProviderPermanentError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Retry decorator
# ---------------------------------------------------------------------------
# Matches §19.3 exactly:
#   Attempt 1 — immediate (no wait before the FIRST retry)
#   Attempt 2 — wait 2 s  (multiplier=2, min=2, max=8 → 2^1=2)
#   Attempt 3 — wait 4 s  (2^2=4)
#   Attempt 4 — wait 8 s  (2^3=8)
#   Attempt 5 — raises RetryError → Fallback Strategy takes over
#
# wait_exponential(multiplier=2, min=2, max=8) produces waits of
# 2 s, 4 s, 8 s for the 2nd, 3rd, and 4th retry respectively,
# matching the LLD table precisely.
# ---------------------------------------------------------------------------


class RetryManager:
    """
    Utility class for applying the EduScribe AI retry strategy.

    Wraps any async callable with the LLD-defined exponential backoff
    policy (§19). Used by llm_manager.py before delegating to
    fallback_manager.py.

    Design notes:
        - Tenacity is used as the underlying retry library (§23 Technology Stack).
        - Only ProviderTransientError triggers retry. ProviderPermanentError
          fails fast — no retry (§19.3 Transient vs. Permanent Failures).
        - RetryError (tenacity) is caught by fallback_manager and treated
          as the signal to switch providers (§19 → §20 escalation).
    """

    # Exponential backoff schedule from LLD §19.3
    MAX_ATTEMPTS: int = 4
    WAIT_MULTIPLIER: float = 2.0
    WAIT_MIN_SECONDS: float = 2.0
    WAIT_MAX_SECONDS: float = 8.0

    async def execute_with_retry(
        self,
        provider_name: str,
        call: Callable[..., Awaitable[Any]],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Execute `call(*args, **kwargs)` with exponential backoff retry.

        Args:
            provider_name: Used in log messages for observability.
            call:          An async callable (e.g., provider.generate).
            *args, **kwargs: Forwarded to `call`.

        Returns:
            The return value of `call` on success.

        Raises:
            ProviderPermanentError: Immediately, with no retry.
            RetryError:             When all 4 retry attempts are exhausted,
                                    signalling the fallback_manager to switch
                                    providers.
        """
        @retry(
            reraise=True,
            stop=stop_after_attempt(self.MAX_ATTEMPTS),
            wait=wait_exponential(
                multiplier=self.WAIT_MULTIPLIER,
                min=self.WAIT_MIN_SECONDS,
                max=self.WAIT_MAX_SECONDS,
            ),
            retry=retry_if_exception_type(ProviderTransientError),
            before_sleep=before_sleep_log(logger, logging.WARNING),
        )
        async def _inner() -> Any:
            try:
                return await call(*args, **kwargs)
            except ProviderPermanentError:
                # Permanent errors bypass retry entirely
                logger.error(
                    "retry_manager: permanent error from provider '%s' — failing immediately",
                    provider_name,
                )
                raise
            except ProviderTransientError as exc:
                # Transient errors will be retried by tenacity
                logger.warning(
                    "retry_manager: transient error from provider '%s': %s "
                    "— will retry with exponential backoff",
                    provider_name,
                    exc,
                )
                raise

        try:
            return await _inner()
        except RetryError:
            logger.warning(
                "retry_manager: all %d retry attempts exhausted for provider '%s' "
                "— escalating to Fallback Strategy (§20)",
                self.MAX_ATTEMPTS,
                provider_name,
            )
            raise
