"""
retry_manager.py — Intra-Provider Retry Logic

Implements the intelligent Retry Strategy described in the final fallback doc.
- 429 Rate Limit: Immediately try the next key (no exponential backoff sleep).
- 5xx / Timeout: Retry exactly once with a 1-second delay, then escalate to fallback.
- Permanent Errors (400, 401, 403, 404): Fail fast, bypass retries, and escalate.
"""

import logging
import asyncio
from typing import Any, Callable, Awaitable
from .base_provider import (
    ProviderTransientError, ProviderPermanentError,
    ProviderServiceError, ProviderRateLimitError
)

logger = logging.getLogger(__name__)

class ExhaustedKeysError(Exception):
    """Raised by llm_manager when no active keys remain for a provider/model."""
    pass

class RetryManager:
    """
    Utility class for applying the EduScribe AI retry strategy.
    
    Replaces Tenacity with a precise, deterministic retry loop that respects
    the exact error classifications from the error_handler.
    """

    MAX_5XX_RETRIES: int = 1

    async def execute_with_retry(
        self,
        provider_name: str,
        call: Callable[..., Awaitable[Any]],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        
        service_error_count = 0

        while True:
            try:
                # `call` is `_call_provider` in `llm_manager.py`.
                return await call(*args, **kwargs)
                
            except ExhaustedKeysError as e:
                # We have no keys left for this provider/model.
                # Break out and let fallback_manager switch providers/models.
                logger.warning(f"retry_manager: {e}")
                raise
                
            except ProviderPermanentError as exc:
                # 400, 401, 403, 404, validation errors
                # These are permanent for this specific request + model + key.
                # Just raise it so fallback_manager can catch it and try the next model.
                logger.error(f"retry_manager: permanent error from {provider_name} — failing fast: {exc}")
                raise
                
            except ProviderRateLimitError as exc:
                # 429 Rate Limit
                # Key is already in a 60s cooldown (done by error_handler).
                # Loop again to immediately fetch the next healthy key from key_manager.
                logger.info(f"retry_manager: 429 RateLimit on {provider_name}, instantly switching keys...")
                continue
                
            except ProviderServiceError as exc:
                # 5xx or Timeout
                service_error_count += 1
                if service_error_count > self.MAX_5XX_RETRIES:
                    logger.warning(
                        f"retry_manager: Exhausted 5xx retries ({self.MAX_5XX_RETRIES}) for {provider_name} "
                        "— escalating to Fallback Strategy"
                    )
                    raise
                
                logger.info(f"retry_manager: 5xx on {provider_name}, waiting 1.0s before retry {service_error_count}...")
                await asyncio.sleep(1.0)
                continue
                
            except ProviderTransientError as exc:
                # Any other unexpected transient error. Fallback immediately to save quota/time.
                logger.warning(f"retry_manager: unexpected transient error on {provider_name}: {exc}")
                raise
