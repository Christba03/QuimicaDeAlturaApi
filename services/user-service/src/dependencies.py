from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

# These are set by main.py during startup
_async_session = None
_redis_client: aioredis.Redis | None = None


def set_session_factory(session_factory):
    global _async_session
    _async_session = session_factory


def set_redis_client(client: aioredis.Redis):
    global _redis_client
    _redis_client = client


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    assert _async_session is not None, "Session factory not initialized"
    async with _async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_redis() -> aioredis.Redis:
    assert _redis_client is not None, "Redis client not initialized"
    return _redis_client
