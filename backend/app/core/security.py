import secrets
from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash
from redis.asyncio import Redis

from app.core.config import settings

_password_hash = PasswordHash.recommended()

REFRESH_COOKIE_NAME = "librachieve_refresh"
_REFRESH_KEY_PREFIX = "refresh:"


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return _password_hash.verify(password, hashed)


def create_access_token(user_id: int, role: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """Raises jwt.PyJWTError if the token is invalid or expired."""
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Not an access token")
    return payload


# Refresh tokens are opaque random strings stored in Redis so they can be revoked.
async def create_refresh_token(redis: Redis, user_id: int) -> str:
    token = secrets.token_urlsafe(48)
    ttl = settings.refresh_token_expire_days * 24 * 3600
    await redis.set(f"{_REFRESH_KEY_PREFIX}{token}", str(user_id), ex=ttl)
    return token


async def consume_refresh_token(redis: Redis, token: str) -> int | None:
    """Returns the user id and deletes the token (rotation), or None if invalid."""
    user_id = await redis.getdel(f"{_REFRESH_KEY_PREFIX}{token}")
    return int(user_id) if user_id else None


async def revoke_refresh_token(redis: Redis, token: str) -> None:
    await redis.delete(f"{_REFRESH_KEY_PREFIX}{token}")
