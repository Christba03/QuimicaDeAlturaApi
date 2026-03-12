"""Shared fixtures for auth-service tests."""
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.rate_limit_service import RateLimitService


@pytest.fixture(autouse=True)
def mock_lifespan_connections():
    """Prevent the app lifespan from connecting to postgres/redis during tests."""
    mock_conn = AsyncMock()
    mock_conn.run_sync = AsyncMock()

    @asynccontextmanager
    async def _mock_begin():
        yield mock_conn

    mock_engine = MagicMock()
    mock_engine.begin = _mock_begin
    mock_engine.dispose = AsyncMock()

    mock_redis = AsyncMock()
    mock_redis.aclose = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)   # so is_ip_locked returns False

    allow_all = AsyncMock(return_value=(True, 99, 60))

    with patch("src.main.engine", mock_engine), \
         patch("src.main.from_url", return_value=mock_redis), \
         patch("arq.create_pool", return_value=AsyncMock()), \
         patch("src.services.email_queue.create_pool", return_value=AsyncMock()), \
         patch.object(RateLimitService, "check_rate_limit", allow_all):
        yield
