"""
core/rate_limiter.py — Per-User Sliding Window Rate Limiter

Uses Redis to track upload counts per user per action per hour.
Falls back gracefully to an in-memory counter when Redis is unavailable
(e.g., during local development without Docker).

Applied as a FastAPI dependency on upload-heavy endpoints.
"""
import logging
import time
from collections import defaultdict

from fastapi import Depends, HTTPException, status

from core.config import settings
from core.security import get_current_user
from models.user import User

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory fallback (used when Redis is not configured)
# Key: (user_id, action)  →  list of UNIX timestamps (floats)
# ---------------------------------------------------------------------------
_memory_store: dict[tuple, list] = defaultdict(list)


_redis_pool = None

def _get_redis():
    """
    Lazily connect to Redis using a connection pool. Returns None if REDIS_URL 
    is not set or Redis is unreachable, triggering the in-memory fallback.
    (ISSUE-018, ISSUE-019 fix)
    """
    global _redis_pool
    redis_url = getattr(settings, "REDIS_URL", None)
    if not redis_url:
        return None
    try:
        import redis as redis_lib  # type: ignore

        if _redis_pool is None:
            _redis_pool = redis_lib.ConnectionPool.from_url(
                redis_url, decode_responses=True, socket_connect_timeout=1
            )
        
        r = redis_lib.Redis(connection_pool=_redis_pool)
        r.ping()
        return r
    except Exception as exc:
        logger.warning("rate_limiter: Redis unavailable (%s) — using in-memory fallback.", exc)
        return None


def _check_limit_memory(user_id: str, action: str, max_per_hour: int) -> None:
    """In-memory sliding window fallback (single-process only)."""
    key = (user_id, action)
    now = time.time()
    window_start = now - 3600  # 1-hour window

    # Prune old entries
    _memory_store[key] = [t for t in _memory_store[key] if t > window_start]

    if len(_memory_store[key]) >= max_per_hour:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: max {max_per_hour} {action} requests per hour.",
        )

    _memory_store[key].append(now)


def _check_limit_redis(r, user_id: str, action: str, max_per_hour: int) -> None:
    """Redis sliding window: ZADD + ZREMRANGEBYSCORE + ZCARD."""
    key = f"rate:{action}:{user_id}"
    now = time.time()
    window_start = now - 3600

    pipe = r.pipeline()
    pipe.zremrangebyscore(key, "-inf", window_start)  # prune old entries
    pipe.zadd(key, {str(now): now})                   # record this request
    pipe.zcard(key)                                    # count in window
    pipe.expire(key, 3600)                             # auto-expire key
    _, _, count, _ = pipe.execute()

    if count > max_per_hour:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: max {max_per_hour} {action} requests per hour.",
        )


def _enforce(user_id: str, action: str, max_per_hour: int) -> None:
    """Enforce rate limit using Redis (with in-memory fallback)."""
    r = _get_redis()
    if r:
        _check_limit_redis(r, user_id, action, max_per_hour)
    else:
        _check_limit_memory(user_id, action, max_per_hour)


# ---------------------------------------------------------------------------
# FastAPI dependency factories
# ---------------------------------------------------------------------------

def upload_rate_limit(current_user: User = Depends(get_current_user)) -> None:
    """
    Dependency: enforce MAX_UPLOADS_PER_HOUR for file-upload endpoint.
    Raise 429 if the user has exceeded their hourly upload allowance.
    """
    _enforce(
        str(current_user.id),
        action="upload",
        max_per_hour=settings.MAX_UPLOADS_PER_HOUR,
    )


def youtube_rate_limit(current_user: User = Depends(get_current_user)) -> None:
    """
    Dependency: enforce MAX_YOUTUBE_PER_HOUR for YouTube submission endpoint.
    Raise 429 if the user has exceeded their hourly YouTube allowance.
    """
    _enforce(
        str(current_user.id),
        action="youtube",
        max_per_hour=settings.MAX_YOUTUBE_PER_HOUR,
    )
