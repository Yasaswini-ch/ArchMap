from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    current_user_from_bearer,
    is_refresh_session_valid,
    revoke_refresh_session,
    store_refresh_session,
)
from app.core.security import create_jwt, decode_jwt
from app.database.postgres import get_async_session
from app.models.core import User
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    Token,
)
from app.services.auth import authenticate_user, create_user, get_user_by_email

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _ttl_seconds(expires_at: datetime) -> int:
    now = datetime.now(timezone.utc)
    return max(0, int((expires_at - now).total_seconds()))


async def _issue_tokens_for_user(user: User) -> Token:
    access_token, access_expires_at, _ = create_jwt(user.email, minutes=15, typ="access")
    refresh_token, refresh_expires_at, refresh_jti = create_jwt(user.email, days=7, typ="refresh")
    await store_refresh_session(str(user.id), refresh_jti, _ttl_seconds(refresh_expires_at))
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        access_expires_at=access_expires_at,
        refresh_expires_at=refresh_expires_at,
    )


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, session: AsyncSession = Depends(get_async_session)):
    existing = await get_user_by_email(session, payload.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    user = await create_user(session, email=payload.email, password=payload.password, full_name=payload.full_name)
    return await _issue_tokens_for_user(user)


@router.post("/login", response_model=Token)
async def login(payload: LoginRequest, session: AsyncSession = Depends(get_async_session)):
    user = await authenticate_user(session, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return await _issue_tokens_for_user(user)


@router.post("/refresh", response_model=Token)
async def refresh(payload: RefreshRequest, session: AsyncSession = Depends(get_async_session)):
    try:
        decoded = decode_jwt(payload.refresh_token)
        if decoded.get("typ") != "refresh":
            raise ValueError("Not a refresh token")
        jti = decoded.get("jti")
        sub = decoded.get("sub")
        if not jti or not sub:
            raise ValueError("Invalid token payload")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if not await is_refresh_session_valid(jti):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh session expired or revoked")

    # Rotate: revoke old and issue new tokens
    await revoke_refresh_session(jti)

    # Fetch user id by email (subject)
    user = await get_user_by_email(session, sub)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found for token subject")

    access_token, access_expires_at, _ = create_jwt(sub, minutes=15, typ="access")
    refresh_token, refresh_expires_at, new_jti = create_jwt(sub, days=7, typ="refresh")

    # Store new refresh session with TTL
    await store_refresh_session(str(user.id), new_jti, _ttl_seconds(refresh_expires_at))

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        access_expires_at=access_expires_at,
        refresh_expires_at=refresh_expires_at,
    )


@router.post("/logout")
async def logout(payload: LogoutRequest):
    try:
        decoded = decode_jwt(payload.refresh_token)
        if decoded.get("typ") != "refresh":
            raise ValueError("Not a refresh token")
        jti = decoded.get("jti")
        if not jti:
            raise ValueError("Missing jti")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    await revoke_refresh_session(jti)
    return {"detail": "logged out"}


@router.get("/me")
async def me(current_user: User = Depends(current_user_from_bearer)):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
    }
