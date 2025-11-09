from __future__ import annotations

import ipaddress
from datetime import timedelta
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.security import decode_jwt
from app.database.redis import get_redis
from app.database.postgres import get_async_session
from app.models.core import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


# Refresh token session management in Redis
# Keys: refresh:<jti> -> user_id, TTL = refresh expiration
# Optional set per user to track active JTIs: user_refresh:<user_id> -> set(jti)


async def store_refresh_session(user_id: str, jti: str, ttl_seconds: int) -> None:
    r = get_redis()
    await r.setex(f"refresh:{jti}", ttl_seconds, user_id)
    await r.sadd(f"user_refresh:{user_id}", jti)
    await r.expire(f"user_refresh:{user_id}", ttl_seconds)


async def revoke_refresh_session(jti: str) -> None:
    r = get_redis()
    key = f"refresh:{jti}"
    user_id = await r.get(key)
    if user_id:
        await r.srem(f"user_refresh:{user_id}", jti)
    await r.delete(key)


async def is_refresh_session_valid(jti: str) -> bool:
    r = get_redis()
    return await r.exists(f"refresh:{jti}") == 1


# Rate limiting middleware (per minute)
class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            auth_header = request.headers.get("authorization", "")
            user_key: Optional[str] = None
            if auth_header.lower().startswith("bearer "):
                token = auth_header.split(" ", 1)[1]
                payload = decode_jwt(token)
                sub = payload.get("sub")
                if sub:
                    user_key = f"user:{sub}"
        except Exception:
            user_key = None

        if not user_key:
            client_ip = request.client.host if request.client else "0.0.0.0"
            try:
                ipaddress.ip_address(client_ip)
            except ValueError:
                client_ip = "0.0.0.0"
            user_key = f"anon:{client_ip}"

        r = get_redis()
        key = f"ratelimit:{user_key}:{int(request.app.state.startup_epoch_min)}"
        count = await r.incr(key)
        if count == 1:
            await r.expire(key, 60)
        if count > settings.RATE_LIMIT_PER_MINUTE:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")

        return await call_next(request)


# Current user dependency from Bearer token
_bearer_scheme = HTTPBearer(auto_error=False)


async def current_user_from_bearer(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    session: AsyncSession = Depends(get_async_session),
) -> User:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_jwt(credentials.credentials)
        sub: str | None = payload.get("sub")
        if not sub:
            raise ValueError("Invalid token")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await session.execute(select(User).where(User.email == sub))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive or missing user")
    return user
