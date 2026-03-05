from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

# Set by main.py at startup
_async_session_factory = None


def set_session_factory(factory):
    global _async_session_factory
    _async_session_factory = factory


# Exposed for workers that need the factory directly
async_session_factory = property(lambda: _async_session_factory)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    assert _async_session_factory is not None, "Session factory not initialized"
    async with _async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
