import time

import redis.asyncio as redis
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.config import settings

logger = structlog.get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple Redis-based sliding-window rate limiter.

    Each client (identified by IP) is allowed ``settings.rate_limit_requests``
    requests within a rolling window of ``settings.rate_limit_window_seconds``.
    """

    def __init__(self, app):
        super().__init__(app)
        self._redis: redis.Redis | None = None

    async def _get_redis(self) -> redis.Redis | None:
        if self._redis is None:
            try:
                self._redis = redis.from_url(
                    settings.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=2,
                )
                await self._redis.ping()
            except Exception:
                logger.warning("redis_unavailable", detail="Rate limiting disabled")
                self._redis = None
        return self._redis

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health / metrics
        if request.url.path in ("/health", "/metrics"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        redis_client = await self._get_redis()

        if redis_client is None:
            # If Redis is down, let the request through rather than blocking everyone.
            return await call_next(request)

        key = f"rate_limit:{client_ip}"
        window = settings.rate_limit_window_seconds
        max_requests = settings.rate_limit_requests
        now = time.time()

        try:
            pipe = redis_client.pipeline()
            # Remove entries older than the window
            pipe.zremrangebyscore(key, 0, now - window)
            # Add the current request timestamp
            pipe.zadd(key, {str(now): now})
            # Count requests in the window
            pipe.zcard(key)
            # Ensure the key expires so we don't leak memory
            pipe.expire(key, window)
            results = await pipe.execute()

            request_count = results[2]
        except Exception:
            logger.warning("rate_limit_check_failed")
            # Fail open
            return await call_next(request)

        if request_count > max_requests:
            logger.info("rate_limit_exceeded", client_ip=client_ip, count=request_count)
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please try again later."},
                headers={"Retry-After": str(window)},
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(max(0, max_requests - request_count))
        return response
