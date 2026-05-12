from __future__ import annotations

import os

import redis as _redis

_client: _redis.Redis | None = None


def get_redis() -> _redis.Redis | None:
    """Return a shared Redis client, or None if REDIS_URL is not set."""
    global _client
    if _client is None:
        url = os.getenv("REDIS_URL", "")
        if not url:
            return None
        _client = _redis.from_url(
            url,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
    return _client
