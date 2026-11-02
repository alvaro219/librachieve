"""Fixed-window rate limiting backed by Redis (shared by every API process)."""

from fastapi import Depends, HTTPException, Request, status
from redis.asyncio import Redis

from app.core.redis import get_redis


def client_ip(request: Request) -> str:
    # Behind Caddy, uvicorn's --proxy-headers already resolved X-Forwarded-For into client.host
    return request.client.host if request.client else "unknown"


async def hit(redis: Redis, key: str, limit: int, window_seconds: int) -> None:
    """Count one hit for `key`; raise 429 once `limit` is exceeded within the window."""
    full_key = f"ratelimit:{key}"
    count = await redis.incr(full_key)
    if count == 1:
        await redis.expire(full_key, window_seconds)
    if count > limit:
        retry = await redis.ttl(full_key)
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Demasiados intentos. Espera unos minutos y vuelve a probar.",
            headers={"Retry-After": str(max(retry, 1))},
        )


def limit_by_ip(name: str, limit: int, window_seconds: int):
    """Dependency: at most `limit` requests per client IP per window for this endpoint."""

    async def dependency(request: Request, redis: Redis = Depends(get_redis)) -> None:
        await hit(redis, f"{name}:ip:{client_ip(request)}", limit, window_seconds)

    return Depends(dependency)
