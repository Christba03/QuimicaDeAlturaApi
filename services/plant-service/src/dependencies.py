from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

_async_session_factory = None
_redis_client: Redis | None = None


def set_session_factory(factory):
    global _async_session_factory
    _async_session_factory = factory


def set_redis_client(client: Redis):
    global _redis_client
    _redis_client = client


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    assert _async_session_factory is not None, "Session factory not initialized"
    async with _async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_redis() -> Redis | None:
    return _redis_client
