from arq import ArqRedis, create_pool
from arq.connections import RedisSettings

from app.core.config import settings

redis_settings = RedisSettings.from_dsn(settings.redis_url)

_pool: ArqRedis | None = None


async def get_queue() -> ArqRedis:
    global _pool
    if _pool is None:
        _pool = await create_pool(redis_settings)
    return _pool


async def close_queue() -> None:
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None
