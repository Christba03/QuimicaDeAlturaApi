import structlog
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.config import settings
from src.services.rate_limit_service import RateLimitService

logger = structlog.get_logger()


def get_client_identifier(request: Request) -> str:
    """Get identifier for rate limiting (IP address or user ID)."""
    # Try to get user ID from request state (if authenticated)
    if hasattr(request.state, "user_id"):
        return f"user:{request.state.user_id}"
    
    # Fall back to IP address
    client_ip = request.client.host if request.client else "unknown"
    return f"ip:{client_ip}"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests."""

    def __init__(self, app: ASGIApp, rate_limit_service: RateLimitService):
        super().__init__(app)
        self.rate_limit_service = rate_limit_service

    async def dispatch(self, request: Request, call_next):
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        # Skip rate limiting for health checks and metrics
        if request.url.path in ["/health", "/metrics", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        identifier = get_client_identifier(request)
        
        # Default rate limit: 100 requests per minute per identifier
        limit = 100
        window = 60
        
        # Apply stricter limits to auth endpoints
        if request.url.path.startswith("/api/v1/auth/login"):
            limit = settings.RATE_LIMIT_LOGIN_PER_15MIN
            window = 15 * 60  # 15 minutes
        elif request.url.path.startswith("/api/v1/auth/register"):
            limit = settings.RATE_LIMIT_REGISTER_PER_HOUR
            window = 60 * 60  # 1 hour
        elif request.url.path.startswith("/api/v1/auth/password/reset"):
            limit = settings.RATE_LIMIT_PASSWORD_RESET_PER_HOUR
            window = 60 * 60  # 1 hour
        elif request.url.path.startswith("/api/v1/auth/verify-email") or request.url.path.startswith("/api/v1/auth/resend-verification"):
            limit = settings.RATE_LIMIT_VERIFICATION_PER_HOUR
            window = 60 * 60  # 1 hour

        is_allowed, remaining, reset_after = await self.rate_limit_service.check_rate_limit(
            identifier, limit, window
        )

        # Add rate limit headers
        response = await call_next(request) if is_allowed else None
        
        if not is_allowed:
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": reset_after,
                },
            )

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_after)
        
        if not is_allowed:
            response.headers["Retry-After"] = str(reset_after)

        return response
