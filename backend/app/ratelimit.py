from __future__ import annotations

import os
import time

import redis

from app.redis_client import get_redis

_LIMIT = int(os.getenv("MCP_RATE_LIMIT", "60"))
_WINDOW = int(os.getenv("MCP_RATE_WINDOW", "60"))


def check(business_id: int) -> tuple[bool, int]:
    """Sliding-window rate check. Returns (allowed, remaining).

    Uses Redis sorted sets — each request is a member scored by its timestamp.
    Members older than the window are pruned before counting.
    Falls back to (True, -1) if Redis is unavailable.
    """
    r = get_redis()
    if r is None:
        return True, -1

    key = f"mcp:rl:{business_id}"
    now = time.time()
    window_start = now - _WINDOW

    try:
        pipe = r.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, _WINDOW)
        results = pipe.execute()

        count_before = results[1]
        remaining = max(0, _LIMIT - count_before - 1)
        return count_before < _LIMIT, remaining
    except redis.RedisError:
        return True, -1
