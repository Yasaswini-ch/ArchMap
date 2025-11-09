from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.postgres import get_async_session
from app.schemas.core import UserRead
from app.services.auth import get_current_user
from app.services.users import get_user, list_users

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def read_me(current_user=Depends(get_current_user)):
    return UserRead.model_validate(current_user)


@router.get("/", response_model=list[UserRead])
async def read_users(limit: int = 50, offset: int = 0, session: AsyncSession = Depends(get_async_session)):
    users = await list_users(session, limit=limit, offset=offset)
    return [UserRead.model_validate(u) for u in users]


@router.get("/{user_id}", response_model=UserRead)
async def read_user(user_id: UUID, session: AsyncSession = Depends(get_async_session)):
    user = await get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserRead.model_validate(user)
