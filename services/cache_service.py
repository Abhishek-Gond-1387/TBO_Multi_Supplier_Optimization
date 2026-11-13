"""Fail-open local TTL cache with optional Redis L2 storage."""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable
from typing import Any

_memory: dict[str, tuple[float, str]] = {}
_redis_client = None


def _redis():
    global _redis_client
    if os.getenv("USE_REDIS", "false").lower() not in {"true", "1", "yes"}:
        return None
    if _redis_client is None:
        try:
            import redis

            _redis_client = redis.Redis.from_url(
                os.getenv("REDIS_URL", "redis://localhost:6379/0"),
                decode_responses=True,
                socket_connect_timeout=0.25,
                socket_timeout=0.25,
            )
        except ImportError:
            return None
    return _redis_client


def get_or_set(key: str, ttl_seconds: int, loader: Callable[[], Any]) -> Any:
    now = time.monotonic()
    local = _memory.get(key)
    if local and local[0] > now:
        return json.loads(local[1])
    client = _redis()
    if client:
        try:
            cached = client.get(key)
            if cached is not None:
                _memory[key] = (now + ttl_seconds, cached)
                return json.loads(cached)
        except Exception:
            pass  # Redis is an optimization; the API remains available without it.
    result = loader()
    encoded = json.dumps(result, separators=(",", ":"), default=str)
    _memory[key] = (now + ttl_seconds, encoded)
    if client:
        try:
            client.setex(key, ttl_seconds, encoded)
        except Exception:
            pass
    return result


def invalidate(*keys: str) -> None:
    for key in keys:
        _memory.pop(key, None)
    client = _redis()
    if client and keys:
        try:
            client.delete(*keys)
        except Exception:
            pass


def invalidate_hotel_caches(canonical_id: str) -> None:
    invalidate(
        f"hotel:canonical:{canonical_id}",
        f"hotel:rates:{canonical_id}",
    )


def cache_status() -> dict[str, bool]:
    client = _redis()
    if client is None:
        return {"memory": True, "redis_configured": False, "redis_connected": False}
    try:
        client.ping()
        return {"memory": True, "redis_configured": True, "redis_connected": True}
    except Exception:
        return {"memory": True, "redis_configured": True, "redis_connected": False}
