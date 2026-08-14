"""
quota_tracker.py — Redis-Backed Quota State per Provider

Tracks how much of each provider's free-tier daily quota has been used,
preventing unnecessary calls to providers whose quota is already exhausted.
Backed by Redis so quota state is shared across all Celery workers — a key
point given that multiple workers may run simultaneously and need consistent
quota visibility.

LLD Reference: §15.1 The Four-Tier Waterfall
               §15.4 Internal Workflow — "Quota Tracker: which tier has quota?"
               §15.5 Advantages — "Quota-aware scheduling"
               §15.6 Limitations — "Daily quota ceilings"
               §18.3 Routing Decision Workflow

# Redis key schema:
#     quota:{provider}:tokens_today     → int (tokens consumed today)
#     quota:{provider}:rpd_today        → int (requests consumed today)
#     quota:{provider}:key_exhausted:{key_n}  → "1" (set when key N is exhausted)
#
# All keys expire at midnight UTC (quota reset time for most free tiers).
"""

import logging
import time
from typing import Optional, List, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class QuotaPolicy:
    provider: str
    model: Optional[str] = None
    requests_per_minute: Optional[int] = None
    requests_per_day: Optional[int] = None
    tokens_per_day: Optional[int] = None
    metering_style: str = "request_token"
    reset_timezone: Optional[str] = None

# ---------------------------------------------------------------------------
# Free-tier daily limits per provider, sourced from LLD §15.2 and §18.11.
# These are approximate — always verify against the official dashboard.
# format: (requests_per_minute, requests_per_day, tokens_per_day)
# None means "unlimited" or "not separately capped".
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Free-tier daily limits per provider, sourced from LLD §15.2 and §18.11.
# These are approximate — always verify against the official dashboard.
# ---------------------------------------------------------------------------
PROVIDER_QUOTA_POLICIES: List[QuotaPolicy] = [
    QuotaPolicy(
        provider="groq",
        model=None, # Default
        requests_per_minute=30,
        requests_per_day=14_400,
        tokens_per_day=500_000,
    ),
    QuotaPolicy(
        provider="groq",
        model="llama-3.3-70b-versatile",
        requests_per_minute=30,
        requests_per_day=1_000,
        tokens_per_day=100_000,
    ),
    QuotaPolicy(
        provider="cloudflare",
        metering_style="compute_credit"
    ),
    QuotaPolicy(
        provider="jina",
        metering_style="one_time_balance",
        tokens_per_day=10_000_000
    ),
    QuotaPolicy(
        provider="cohere",
        metering_style="monthly_call_cap",
        requests_per_minute=20,
        requests_per_day=1_000
    ),
    QuotaPolicy(
        provider="openrouter",
        metering_style="flat_daily_cap",
        requests_per_minute=20,
        requests_per_day=50
    ),
    QuotaPolicy(
        provider="gemini",
        metering_style="request_token",
        reset_timezone="America/Los_Angeles",
        requests_per_minute=15,
        requests_per_day=1_500,
        tokens_per_day=None
    )
]

def get_quota_policy(provider: str, model: Optional[str] = None) -> QuotaPolicy:
    best_match = None
    default_match = None
    
    for policy in PROVIDER_QUOTA_POLICIES:
        if policy.provider == provider:
            if policy.model == model:
                best_match = policy
            if policy.model is None:
                default_match = policy
                
    return best_match or default_match or QuotaPolicy(provider=provider)


class QuotaTracker:
    """
    Redis-backed quota state tracker.

    Tracks per-provider request counts and token usage so the LLM Manager
    can skip providers that have exhausted their free-tier quota.

    When Redis is unavailable (e.g., local development without Redis),
    the tracker falls back to an in-memory store and logs a warning.
    This allows the LLM pipeline to continue functioning in development
    without requiring Redis to be running.

    LLD Reference: §15 LLM Provider Architecture — "quota_tracker.py:
    Redis-backed quota state per provider"
    """

    def __init__(self, redis_url: Optional[str] = None) -> None:
        """
        Args:
            redis_url: Redis connection URL, e.g. "redis://localhost:6379/0".
                       Loaded from REDIS_URL environment variable if None.
        """
        self._redis = None
        self._in_memory: dict[str, dict] = {}  # fallback when Redis is down

        self._connect_redis(redis_url)

    def _connect_redis(self, redis_url: Optional[str]) -> None:
        """Attempt to connect to Redis; fall back to in-memory on failure."""
        import os
        url = redis_url or os.environ.get(
            "REDIS_URL", "redis://localhost:6379/0")
        try:
            import redis as redis_lib
            self._redis = redis_lib.from_url(url, decode_responses=True)
            self._redis.ping()
            logger.info("quota_tracker: connected to Redis at %s", url)
        except Exception as exc:
            logger.warning(
                "quota_tracker: Redis unavailable (%s) — using in-memory fallback. "
                "Quota state will NOT be shared across workers.",
                exc,
            )
            self._redis = None

    # ---------------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------------

    def has_quota(self, provider: str, model: Optional[str] = None) -> bool:
        """Check if a provider/model currently has available quota."""
        policy = get_quota_policy(provider, model)
        has = True

        if policy.requests_per_day is not None:
            used_rpd = self._get_rpd_used(provider)
            if used_rpd >= policy.requests_per_day:
                has = False
                logger.info("quota_tracker: provider '%s' has exhausted RPD quota (%d / %d requests today)", provider, used_rpd, policy.requests_per_day)

        if has and policy.tokens_per_day is not None:
            used_tokens = self._get_tokens_used(provider)
            if used_tokens >= policy.tokens_per_day:
                has = False
                logger.info("quota_tracker: provider '%s' has exhausted Token quota (%d / %d tokens today)", provider, used_tokens, policy.tokens_per_day)

        return has

    def record_request(
        self,
        provider: str,
        model: Optional[str] = None,
        tokens_used: int = 0,
    ) -> None:
        """
        Increment the request and token counters for a provider.

        Called after a successful LLM response is received.

        Args:
            provider:    Provider name.
            model:       LiteLLM model ID (for per-model tracking).
            tokens_used: Total tokens (prompt + completion) in this request.
        """
        self._increment_rpd(provider)
        if tokens_used > 0:
            self._increment_tokens(provider, tokens_used)

    def get_usage_summary(self, provider: str) -> dict:
        """
        Return a dict summarising today's usage for a provider.
        Used for observability / admin dashboards.
        """
        limits = PROVIDER_FREE_TIER_LIMITS.get(provider, {})
        return {
            "provider": provider,
            "requests_today": self._get_rpd_used(provider),
            "tokens_today": self._get_tokens_used(provider),
            "metering_style": limits.get("metering_style"),
            "has_quota": self.has_quota(provider),
        }

    def reset_daily_counters(self, provider: Optional[str] = None) -> None:
        """
        Reset daily request and token counters.
        Called at midnight UTC when free-tier quotas refresh.

        Args:
            provider: If given, reset only that provider.
                      If None, reset all providers.
        """
        providers_to_reset = (
            [provider]
            if provider
            else list(PROVIDER_FREE_TIER_LIMITS.keys())
        )
        for p in providers_to_reset:
            self._reset_provider(p)
            logger.info(
                "quota_tracker: reset daily counters for provider '%s'", p)

    # ---------------------------------------------------------------------------
    # Internal helpers — Redis vs. in-memory
    # ---------------------------------------------------------------------------

    def _rpd_key(self, provider: str) -> str:
        return f"quota:{provider}:rpd_today"

    def _token_key(self, provider: str) -> str:
        return f"quota:{provider}:tokens_today"

    def _seconds_until_midnight(self, provider: str) -> int:
        """Return seconds remaining until the quota reset."""
        import datetime
        try:
            import pytz
            limits = PROVIDER_FREE_TIER_LIMITS.get(provider, {})
            tz_name = limits.get("reset_timezone", "UTC")
            tz = pytz.timezone(tz_name)
            now = datetime.datetime.now(tz)
            tomorrow = now + datetime.timedelta(days=1)
            midnight = datetime.datetime(tomorrow.year, tomorrow.month, tomorrow.day, tzinfo=tz)
            return max(int((midnight - now).total_seconds()), 1)
        except ImportError:
            # Fallback to UTC math if pytz not installed
            now = time.gmtime()
            remaining = (
                (23 - now.tm_hour) * 3600
                + (59 - now.tm_min) * 60
                + (60 - now.tm_sec)
            )
            return max(remaining, 1)

    def _get_rpd_used(self, provider: str) -> int:
        if self._redis:
            try:
                val = self._redis.get(self._rpd_key(provider))
                return int(val) if val else 0
            except Exception:
                pass
        return self._in_memory.get(provider, {}).get("rpd", 0)

    def _get_tokens_used(self, provider: str) -> int:
        if self._redis:
            try:
                val = self._redis.get(self._token_key(provider))
                return int(val) if val else 0
            except Exception:
                pass
        return self._in_memory.get(provider, {}).get("tokens", 0)

    def _increment_rpd(self, provider: str) -> None:
        if self._redis:
            try:
                pipe = self._redis.pipeline()
                pipe.incr(self._rpd_key(provider))
                pipe.expire(
                    self._rpd_key(provider),
                    self._seconds_until_midnight(provider))
                pipe.execute()
                return
            except Exception:
                pass
        if provider not in self._in_memory:
            self._in_memory[provider] = {"rpd": 0, "tokens": 0}
        self._in_memory[provider]["rpd"] += 1

    def _increment_tokens(self, provider: str, tokens: int) -> None:
        if self._redis:
            try:
                pipe = self._redis.pipeline()
                pipe.incrby(self._token_key(provider), tokens)
                pipe.expire(
                    self._token_key(provider),
                    self._seconds_until_midnight(provider))
                pipe.execute()
                return
            except Exception:
                pass
        if provider not in self._in_memory:
            self._in_memory[provider] = {"rpd": 0, "tokens": 0}
        self._in_memory[provider]["tokens"] += tokens

    def _reset_provider(self, provider: str) -> None:
        if self._redis:
            try:
                self._redis.delete(
                    self._rpd_key(provider),
                    self._token_key(provider))
                return
            except Exception:
                pass
        self._in_memory.pop(provider, None)
