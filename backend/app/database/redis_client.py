from __future__ import annotations

from typing import Optional

from redis.asyncio import Redis

from app.database.redis import get_redis


async def test_connection_async() -> bool:
    try:
        r: Redis = get_redis()
        pong = await r.ping()
        return bool(pong)
    except Exception:
        return False


def get_client() -> Redis:
    return get_redis()


__all__ = [
    "get_client",
    "test_connection_async",
]
