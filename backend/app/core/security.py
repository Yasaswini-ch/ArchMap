from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Tuple

from jose import jwt

from app.core.config import settings
from app.utils.security import get_password_hash, verify_password

# Defaults per spec
ACCESS_TOKEN_MINUTES_DEFAULT = 15
REFRESH_TOKEN_DAYS_DEFAULT = 7


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def create_jwt(subject: str, *, minutes: int | None = None, days: int | None = None, typ: str = "access") -> tuple[str, datetime, str]:
    if minutes is None and days is None:
        minutes = ACCESS_TOKEN_MINUTES_DEFAULT if typ == "access" else REFRESH_TOKEN_DAYS_DEFAULT * 24 * 60
    expire = now_utc() + (timedelta(minutes=minutes) if minutes is not None else timedelta(days=days or 0))
    jti = str(uuid.uuid4())
    payload = {"sub": subject, "exp": int(expire.timestamp()), "jti": jti, "typ": typ}
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, expire, jti


def decode_jwt(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


__all__ = [
    "get_password_hash",
    "verify_password",
    "create_jwt",
    "decode_jwt",
    "ACCESS_TOKEN_MINUTES_DEFAULT",
    "REFRESH_TOKEN_DAYS_DEFAULT",
]
