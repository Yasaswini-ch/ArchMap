from __future__ import annotations

import asyncio
from typing import Optional

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database.postgres import engine, get_async_session, AsyncSession, AsyncSessionLocal


async def test_connection_async() -> bool:
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False


def test_connection() -> bool:
    """Convenience sync wrapper for quick health checks."""
    return asyncio.get_event_loop().run_until_complete(test_connection_async())


__all__ = [
    "engine",
    "get_async_session",
    "AsyncSession",
    "AsyncSessionLocal",
    "test_connection",
    "test_connection_async",
]
