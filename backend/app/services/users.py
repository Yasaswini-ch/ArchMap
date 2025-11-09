from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core import User


async def list_users(session: AsyncSession, *, limit: int = 50, offset: int = 0) -> List[User]:
    result = await session.execute(select(User).offset(offset).limit(limit))
    return list(result.scalars().all())


async def get_user(session: AsyncSession, user_id: UUID) -> Optional[User]:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def delete_user(session: AsyncSession, user_id: UUID) -> bool:
    result = await session.execute(delete(User).where(User.id == user_id))
    await session.commit()
    return result.rowcount > 0
