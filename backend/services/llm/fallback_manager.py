"""
fallback_manager.py — Inter-Provider Fallback Logic

Implements the Fallback Strategy described in §20. When the currently
selected provider exhausts all retries (RetryError from retry_manager)
or all API keys (KeyManager.all_keys_exhausted), the fallback_manager
switches to the next provider in the fixed priority sequence.

The transition is entirely transparent to the calling code — no
manual model switching is ever required.

LLD Reference: §20 Fallback Strategy
               §20.3 Detailed Explanation — Fallback Order
               §20.4 Internal Workflow

Fallback order (§20.3):
    Tier 1: Gemini 2.5 Flash → Gemini 2.5 Flash Lite
            DeepSeek V3 (OpenRouter :free) → Qwen3 235B (OpenRouter :free)
    Tier 2: Cerebras/Llama-4-Scout → Cerebras/Qwen3-32B
            Groq/Llama-3.3-70B → Groq/Qwen3-32B
    Tier 3: Together AI (Llama-3.3-70B-Free) → SambaNova → Mistral Small 3.2
    Tier 4: OpenRouter/free router → Groq/Llama-3.1-8B → Mistral/open-mistral-nemo

Three-layer resilience architecture (LLD §21.3):
    1. API Key Rotation  — try all keys on current provider
    2. Retry Strategy    — exponential backoff on current provider
    3. Fallback Strategy — switch to next provider (this module)
"""

import os
import yaml
import time
import logging
from enum import Enum
from typing import Any, Callable, Awaitable, Optional, Tuple, List, Dict
from dataclasses import dataclass

from tenacity import RetryError
from .provider_stats import ProviderStats

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Four-Tier Waterfall Provider + Model Sequence (Loaded from YAML)
# LLD Reference: §15.1 The Four-Tier Waterfall, §20.3 Fallback Order
# ---------------------------------------------------------------------------
@dataclass
class FallbackModel:
    provider: str
    model: str
    tier: int
    supports_vision: bool
    max_context_window: int

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "litellm_fallback_config.yaml")

def load_fallback_chain() -> List[FallbackModel]:
    try:
        if not os.path.exists(CONFIG_PATH):
            logger.warning(f"Config file not found at {CONFIG_PATH}. Using empty chain.")
            return []
        with open(CONFIG_PATH, "r") as f:
            config = yaml.safe_load(f)
        chain = []
        fallback_cfg = config.get("fallback_chain", {})
        for tier_num, tier_key in enumerate(["tier1", "tier2", "tier3", "tier4"], start=1):
            for entry in fallback_cfg.get(tier_key, []):
                chain.append(FallbackModel(
                    provider=entry.get("provider", ""),
                    model=entry.get("model", ""),
                    tier=tier_num,
                    supports_vision=entry.get("supports_vision", False),
                    max_context_window=entry.get("max_context_window", 8192)
                ))
        return chain
    except Exception as e:
        logger.error(f"Failed to load fallback chain from YAML: {e}")
        return []

FALLBACK_CHAIN: list[FallbackModel] = load_fallback_chain()

class CircuitState(Enum):
    CLOSED = "CLOSED"      # Normal operation
    OPEN = "OPEN"          # Failing, fast-fail requests
    HALF_OPEN = "HALF_OPEN" # Testing if healthy again

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, cooldown_seconds: int = 120, rate_limit_cooldown: int = 60):
        self.state: CircuitState = CircuitState.CLOSED
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.rate_limit_cooldown = rate_limit_cooldown
        self.cooldown_until = 0.0
        
    def record_failure(self, is_rate_limit: bool = False):
        now = time.time()
        if is_rate_limit:
            self.cooldown_until = now + self.rate_limit_cooldown
            logger.warning(f"Circuit breaker activated (Rate Limit). Cooldown for {self.rate_limit_cooldown}s.")
            return
            
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.cooldown_until = now + self.cooldown_seconds
            logger.warning(f"Circuit breaker OPENED. Cooldown for {self.cooldown_seconds}s.")
            
    def record_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.cooldown_until = 0.0
        
    def can_execute(self) -> bool:
        now = time.time()
        if now < self.cooldown_until:
            return False
            
        if self.state == CircuitState.OPEN:
            # Cooldown passed, try half-open
            self.state = CircuitState.HALF_OPEN
            return True
            
        return True


class FallbackManager:
    """
    Inter-provider fallback logic for the EduScribe AI LLM layer.

    Traverses the four-tier waterfall (§15.1, §20.3) when the current
    provider and model fail to produce a successful response after all
    retry attempts and all API keys have been cycled.

    Design notes:
        - The fallback order is fixed and quality-prioritized — the
          pipeline always attempts the highest-quality option first
          and only degrades when genuinely necessary (§20.3).
        - This class never calls an LLM directly; it invokes a
          caller-supplied async callable (provided by llm_manager.py)
          that knows how to build and dispatch the LLM request.
        - If all entries in FALLBACK_CHAIN are exhausted, a
          AllProvidersExhaustedError is raised.

    LLD Reference: §20 Fallback Strategy
    """

    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.stats = ProviderStats()
        
    def _get_circuit_breaker(self, provider: str) -> CircuitBreaker:
        if provider not in self.circuit_breakers:
            self.circuit_breakers[provider] = CircuitBreaker()
        return self.circuit_breakers[provider]

    async def execute_with_fallback(
        self,
        call_fn: Callable[[str, str], Awaitable[Any]],
        quota_tracker: Any,        # QuotaTracker instance
        key_manager: Any,          # KeyManager instance
        retry_manager: Any,        # RetryManager instance
        preferred_provider: Optional[str] = None,
        preferred_model: Optional[str] = None,
        required_vision: bool = False,
        min_context_window: int = 0,
    ) -> Any:
        """
        Try each (provider, model) entry in FALLBACK_CHAIN in order,
        skipping providers whose quota is exhausted or lack capabilities.

        Args:
            call_fn:            Async function (provider, model) → response.
            quota_tracker:      QuotaTracker — used to skip exhausted providers.
            key_manager:        KeyManager — rotates keys before declaring
                                a provider fully exhausted.
            retry_manager:      RetryManager — wraps each call with backoff.
            preferred_provider: If given, try this provider + model first.
            preferred_model:    Paired with preferred_provider.
            required_vision:    If True, skips models that don't support vision.
            min_context_window: Skips models with max_context_window < min_context_window.

        Returns:
            The successful LLM response dict.

        Raises:
            AllProvidersExhaustedError: All entries in the chain failed.
        """
        # Build the chain, optionally injecting a preferred starting point
        chain = list(FALLBACK_CHAIN)
        if preferred_provider and preferred_model:
            # We don't have capability info for a dynamically injected preferred model,
            # so we assume it meets requirements or it wouldn't be preferred.
            preferred_fallback = FallbackModel(
                provider=preferred_provider,
                model=preferred_model,
                tier=0,                    # Highest priority
                supports_vision=True,      # assume True to bypass filter
                max_context_window=2000000 # assume large to bypass filter
            )
            base_chain = [entry for entry in chain if not (entry.provider == preferred_provider and entry.model == preferred_model)]
            base_chain.sort(key=lambda m: (m.tier, -self.stats.calculate_score(m.provider, m.model)))
            chain = [preferred_fallback] + base_chain
        else:
            chain.sort(key=lambda m: (m.tier, -self.stats.calculate_score(m.provider, m.model)))

        last_error: Optional[Exception] = None

        for fallback_model in chain:
            provider = fallback_model.provider
            model = fallback_model.model
            
            # Capability Filtering
            if required_vision and not fallback_model.supports_vision:
                logger.debug(f"fallback_manager: skipping {provider}/{model} — lacks vision capability")
                continue
            if min_context_window > fallback_model.max_context_window:
                logger.debug(f"fallback_manager: skipping {provider}/{model} — insufficient context window ({fallback_model.max_context_window} < {min_context_window})")
                continue
            breaker = self._get_circuit_breaker(provider)
            if not breaker.can_execute():
                logger.debug(
                    "fallback_manager: skipping %s/%s — circuit breaker open/cooldown",
                    provider,
                    model,
                )
                continue

            if not quota_tracker.has_quota(provider):
                logger.debug(
                    "fallback_manager: skipping %s/%s — quota exhausted",
                    provider,
                    model,
                )
                continue

            if key_manager.all_keys_exhausted(provider):
                logger.debug(
                    "fallback_manager: skipping %s/%s — all keys exhausted",
                    provider,
                    model,
                )
                continue

            try:
                logger.info(
                    "fallback_manager: attempting %s / %s",
                    provider,
                    model,
                )
                start_time = time.time()
                result = await retry_manager.execute_with_retry(
                    provider,
                    call_fn,
                    provider,
                    model,
                )
                
                latency = time.time() - start_time
                self.stats.record_call(provider, model, success=True, latency=latency)
                breaker.record_success()
                
                # Record successful request against quota
                tokens_used = (
                    result.get("usage", {}).get("total_tokens", 0)
                    if isinstance(result, dict)
                    else 0
                )
                quota_tracker.record_request(provider, model, tokens_used)
                logger.info(
                    "fallback_manager: success with %s / %s (%d tokens)",
                    provider,
                    model,
                    tokens_used,
                )
                return result

            except RetryError as exc:
                latency = time.time() - start_time
                self.stats.record_call(provider, model, success=False, latency=latency)
                
                is_429 = "429" in str(exc) or "rate limit" in str(exc).lower()
                breaker.record_failure(is_rate_limit=is_429)
                
                logger.warning(
                    "fallback_manager: %s / %s failed after all retries — "
                    "descending to next provider in chain",
                    provider,
                    model,
                )
                last_error = exc
                continue

            except Exception as exc:
                latency = time.time() - start_time
                self.stats.record_call(provider, model, success=False, latency=latency)
                
                breaker.record_failure(is_rate_limit=False)
                logger.error(
                    "fallback_manager: unexpected error from %s / %s: %s",
                    provider,
                    model,
                    exc,
                )
                last_error = exc
                continue

        raise AllProvidersExhaustedError(
            f"All {len(FALLBACK_CHAIN)} entries in the fallback chain failed. "
            "The pipeline will queue this request until quotas reset (midnight UTC). "
            f"Last error: {last_error}"
        )

    @staticmethod
    def get_fallback_chain() -> list[tuple[str, str]]:
        """Return the full fallback chain for inspection / logging."""
        return [(entry.provider, entry.model) for entry in FALLBACK_CHAIN]

    @staticmethod
    def get_tier(provider: str, model: str) -> int:
        """
        Return the tier (1–4) for a given (provider, model) entry,
        or 0 if the entry is not in the chain.
        """
        for entry in FALLBACK_CHAIN:
            if entry.provider == provider and entry.model == model:
                return entry.tier
        return 0


class AllProvidersExhaustedError(Exception):
    """
    Raised when every provider in the four-tier fallback chain has been
    tried and failed. The LLM Manager queues the request for retry after
    the next quota reset (midnight UTC).

    LLD Reference: §15.4 Internal Workflow — "Queue request — retry after quota reset"
    """
