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

import logging
from typing import Any, Callable, Awaitable, Optional

from tenacity import RetryError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Four-Tier Waterfall Provider + Model Sequence
# LLD Reference: §15.1 The Four-Tier Waterfall, §20.3 Fallback Order
#
# Format: (provider_name, litellm_model_id)
# The list is traversed left-to-right; the first entry that has quota
# and succeeds wins. Within each provider, key_manager handles key rotation.
# ---------------------------------------------------------------------------
FALLBACK_CHAIN: list[tuple[str, str]] = [
    # ── Tier 1 — PREMIUM FREE ──────────────────────────────────────────────
    # Rank 1: Gemini 2.5 Pro — Highest quality, 1M context (complex tasks)
    ("gemini",      "gemini/gemini-2.5-pro"),
    # Rank 2: Gemini 2.5 Flash — Fastest Gemini, excellent structured output
    ("gemini",      "gemini/gemini-2.5-flash"),
    # Rank 3: Cohere Command A Plus — Long-context reasoning alternative
    ("cohere",      "cohere/command-a-plus-05-2026"),

    # ── Tier 2 — HIGH-SPEED FREE ───────────────────────────────────────────
    # Rank 4: Groq Llama 3.3 70B — Very fast, high quality (14,400 RPD)
    ("groq",        "groq/llama-3.3-70b-versatile"),
    # Rank 5: Groq Qwen3-32B — Fast reasoning, efficient
    ("groq",        "groq/qwen3-32b"),

    # ── Tier 3 — OPEN-SOURCE BACKUP ───────────────────────────────────────
    # Rank 6: Cohere Command A — Strong long-context understanding
    ("cohere",      "cohere/command-a-03-2025"),
    # Rank 7: Cloudflare Kimi K2.6 — Large context, reliable structured output
    ("cloudflare",  "cloudflare/@cf/moonshotai/kimi-k2.6"),
    # Rank 8: OpenRouter DeepSeek V3 — Free tier capable model
    ("openrouter",  "openrouter/deepseek/deepseek-chat:free"),
    # Rank 9: OpenRouter Qwen3 235B — Free large model
    ("openrouter",  "openrouter/qwen/qwen3-235b-a22b:free"),

    # ── Tier 4 — EMERGENCY FALLBACK ────────────────────────────────────────
    # Rank 10: OpenRouter Llama 3.3 70B — Free emergency fallback
    ("openrouter",  "openrouter/meta-llama/llama-3.3-70b-instruct:free"),
    # Rank 11: OpenRouter Gemma 4 31B — Free high-quality fallback
    ("openrouter",  "openrouter/google/gemma-4-31b-it:free"),
    # Rank 12: Groq Llama 3.1 8B — Smallest, fastest emergency model
    ("groq",        "groq/llama-3.1-8b-instant"),
    # Rank 13: Cloudflare GPT-OSS 120B — Large production fallback
    ("cloudflare",  "cloudflare/@cf/openai/gpt-oss-120b"),
    # Rank 14: Cloudflare GPT-OSS 20B — Final local fallback
    ("cloudflare",  "cloudflare/@cf/openai/gpt-oss-20b"),
]


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

    async def execute_with_fallback(
        self,
        call_fn: Callable[[str, str], Awaitable[Any]],
        quota_tracker: Any,        # QuotaTracker instance
        key_manager: Any,          # KeyManager instance
        retry_manager: Any,        # RetryManager instance
        preferred_provider: Optional[str] = None,
        preferred_model: Optional[str] = None,
    ) -> Any:
        """
        Try each (provider, model) entry in FALLBACK_CHAIN in order,
        skipping providers whose quota is exhausted.

        Args:
            call_fn:            Async function (provider, model) → response.
                                Provided by llm_manager.py.
            quota_tracker:      QuotaTracker — used to skip exhausted providers.
            key_manager:        KeyManager — rotates keys before declaring
                                a provider fully exhausted.
            retry_manager:      RetryManager — wraps each call with backoff.
            preferred_provider: If given, try this provider + model first
                                before consulting the full waterfall.
            preferred_model:    Paired with preferred_provider.

        Returns:
            The successful LLM response dict.

        Raises:
            AllProvidersExhaustedError: All 15 entries in the chain failed.
        """
        # Build the chain, optionally injecting a preferred starting point
        chain = list(FALLBACK_CHAIN)
        if preferred_provider and preferred_model:
            chain = [(preferred_provider, preferred_model)] + [
                entry for entry in chain
                if entry != (preferred_provider, preferred_model)
            ]

        last_error: Optional[Exception] = None

        for provider, model in chain:
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
                result = await retry_manager.execute_with_retry(
                    provider,
                    call_fn,
                    provider,
                    model,
                )
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
                logger.warning(
                    "fallback_manager: %s / %s failed after all retries — "
                    "descending to next provider in chain",
                    provider,
                    model,
                )
                last_error = exc
                continue

            except Exception as exc:
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
        return list(FALLBACK_CHAIN)

    @staticmethod
    def get_tier(provider: str, model: str) -> int:
        """
        Return the tier (1–4) for a given (provider, model) entry,
        or 0 if the entry is not in the chain.
        """
        # Tier 1: entries 0-2 (Gemini ×2, Cohere Command-A-Plus)
        # Tier 2: entries 3-4 (Groq ×2)
        # Tier 3: entries 5-8 (Cohere, Cloudflare, OpenRouter ×2)
        # Tier 4: entries 9-13 (OpenRouter ×2, Groq, Cloudflare ×2)
        tier_boundaries = [3, 5, 9, 14]   # exclusive upper bound for tiers 1–4
        for idx, entry in enumerate(FALLBACK_CHAIN):
            if entry == (provider, model):
                for tier, boundary in enumerate(tier_boundaries, start=1):
                    if idx < boundary:
                        return tier
        return 0


class AllProvidersExhaustedError(Exception):
    """
    Raised when every provider in the four-tier fallback chain has been
    tried and failed. The LLM Manager queues the request for retry after
    the next quota reset (midnight UTC).

    LLD Reference: §15.4 Internal Workflow — "Queue request — retry after quota reset"
    """
