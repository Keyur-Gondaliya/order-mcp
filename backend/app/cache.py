from __future__ import annotations

import hashlib
import json
import os
from typing import Any

import redis

from app.redis_client import get_redis

_TTL = int(os.getenv("MCP_CACHE_TTL", "30"))


def _key(business_id: int, operation: str, params: dict) -> str:
    digest = hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()
    return f"mcp:cache:{business_id}:{operation}:{digest}"


def get(business_id: int, operation: str, params: dict) -> Any | None:
    r = get_redis()
    if r is None:
        return None
    try:
        val = r.get(_key(business_id, operation, params))
        return json.loads(val) if val is not None else None
    except (redis.RedisError, json.JSONDecodeError):
        return None


def put(business_id: int, operation: str, params: dict, value: Any) -> None:
    r = get_redis()
    if r is None:
        return
    try:
        r.setex(_key(business_id, operation, params), _TTL, json.dumps(value))
    except redis.RedisError:
        pass


def invalidate(business_id: int) -> None:
    """Delete all cached entries for a business (called on any write)."""
    r = get_redis()
    if r is None:
        return
    try:
        keys = list(r.scan_iter(f"mcp:cache:{business_id}:*"))
        if keys:
            r.delete(*keys)
    except redis.RedisError:
        pass
