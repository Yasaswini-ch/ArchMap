from __future__ import annotations

from typing import AsyncIterator

from redis.asyncio import Redis

from app.core.config import settings

_redis: Redis | None = None


def get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


async def get_redis_dep() -> AsyncIterator[Redis]:
    client = get_redis()
    try:
        yield client
    finally:
        # Keep the client for reuse; do not close per-request
        pass


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None
