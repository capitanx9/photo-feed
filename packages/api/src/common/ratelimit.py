"""Redis-backed sliding-window rate limiter.

Uses a sorted set per (scope, identity) with the score = unix timestamp.
On each hit we drop stale entries (older than the window), count what's
left, and either reject (>= limit) or add the new hit. Atomic via a
single Lua-equivalent pipeline.

Falls back to in-memory tracking when settings.RATELIMIT_ENABLE is False
(i.e. inside the test suite) so tests don't need Redis running.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

import redis
from django.conf import settings

# ======================================================================
# In-memory backend (tests)
# ======================================================================

_memory_lock = Lock()
_memory_hits: dict[str, deque[float]] = defaultdict(deque)


def _memory_check(*, key: str, limit: int, window_seconds: int) -> bool:
    now = time.time()
    cutoff = now - window_seconds
    with _memory_lock:
        bucket = _memory_hits[key]
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= limit:
            return False
        bucket.append(now)
        return True


# ======================================================================
# Redis backend
# ======================================================================


_redis_client = None


def _get_redis():  # type: ignore[no-untyped-def]
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis.from_url(settings.REDIS_URL)
    return _redis_client


def _redis_check(*, key: str, limit: int, window_seconds: int) -> bool:
    now = time.time()
    cutoff = now - window_seconds
    client = _get_redis()
    pipe = client.pipeline()
    pipe.zremrangebyscore(key, 0, cutoff)
    pipe.zcard(key)
    pipe.zadd(key, {str(now): now})
    pipe.expire(key, window_seconds)
    _, count, _, _ = pipe.execute()
    if count >= limit:
        # rollback the add we just did
        client.zrem(key, str(now))
        return False
    return True


# ======================================================================
# Public entry point
# ======================================================================


def allow(*, scope: str, identity: str, limit: int, window_seconds: int) -> bool:
    """Return True if the action is within the limit and record the hit.

    `scope` is a short namespace (e.g. "ai-generate"); `identity` is the
    per-user/IP id. Tests run with RATELIMIT_ENABLE=False which routes to
    the in-memory backend so they don't require Redis.
    """
    key = f"ratelimit:{scope}:{identity}"
    if settings.RATELIMIT_ENABLE:
        return _redis_check(key=key, limit=limit, window_seconds=window_seconds)
    return _memory_check(key=key, limit=limit, window_seconds=window_seconds)


def reset_memory() -> None:
    """Test helper — clear the in-memory bucket between tests."""
    with _memory_lock:
        _memory_hits.clear()
