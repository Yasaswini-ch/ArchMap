from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.postgres import get_async_session
from app.models.core import User
from app.utils.security import (
    verify_password,
    get_password_hash,
    create_access_token as _create_access_token,
    decode_access_token,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> tuple[str, datetime]:
    minutes = int(expires_delta.total_seconds() // 60) if expires_delta else settings.ACCESS_TOKEN_EXPIRE_MINUTES
    return _create_access_token(subject, minutes)


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create_user(session: AsyncSession, *, email: str, password: str, full_name: Optional[str] = None) -> User:
    user = User(email=email, hashed_password=get_password_hash(password), full_name=full_name)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def authenticate_user(session: AsyncSession, email: str, password: str) -> Optional[User]:
    user = await get_user_by_email(session, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        subject: str | None = payload.get("sub")
        if subject is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await get_user_by_email(session, subject)
    if user is None:
        raise credentials_exception
    return user
