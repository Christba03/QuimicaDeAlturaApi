import structlog
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.config import settings
from src.services.rate_limit_service import RateLimitService

logger = structlog.get_logger()

# Paths that are always exempt from rate limiting
_EXEMPT_PATHS = {"/health", "/healthz", "/readyz", "/metrics", "/docs", "/redoc", "/openapi.json"}


def get_client_ip(request: Request) -> str:
    """Extract the real client IP, respecting X-Forwarded-For from trusted proxies."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_client_identifier(request: Request) -> str:
    """Get identifier for rate limiting (user ID if authenticated, else IP)."""
    if hasattr(request.state, "user_id"):
        return f"user:{request.state.user_id}"
    return f"ip:{get_client_ip(request)}"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting + IP lockout checks."""

    def __init__(self, app: ASGIApp, rate_limit_service: RateLimitService):
        super().__init__(app)
        self.rate_limit_service = rate_limit_service

    async def dispatch(self, request: Request, call_next):
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        path = request.url.path
        if path in _EXEMPT_PATHS:
            return await call_next(request)

        ip_address = get_client_ip(request)

        # --- IP-level lockout check (brute-force protection) ---
        if hasattr(request.app.state, "redis"):
            from src.services.security_service import SecurityService
            security_svc = SecurityService.__new__(SecurityService)  # no DB session needed
            if await security_svc.is_ip_locked(ip_address, request.app.state.redis):
                logger.warning("rate_limit.ip_locked", ip=ip_address, path=path)
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": "Too many failed login attempts from this IP. Please try again later.",
                        "retry_after": settings.IP_LOCKOUT_DURATION_MINUTES * 60,
                    },
                    headers={"Retry-After": str(settings.IP_LOCKOUT_DURATION_MINUTES * 60)},
                )

        # Per-endpoint bucket so limits don't share one counter per IP
        base_id = get_client_identifier(request)
        limit = 100
        window = 60

        if path.startswith("/api/v1/auth/login"):
            limit = settings.RATE_LIMIT_LOGIN_PER_15MIN
            window = 15 * 60
            identifier = f"{base_id}:login"
        elif path.startswith("/api/v1/auth/register"):
            limit = settings.RATE_LIMIT_REGISTER_PER_HOUR
            window = 3600
            identifier = f"{base_id}:register"
        elif path.startswith("/api/v1/auth/password/reset"):
            limit = settings.RATE_LIMIT_PASSWORD_RESET_PER_HOUR
            window = 3600
            identifier = f"{base_id}:password_reset"
        elif path.startswith("/api/v1/auth/verify-email") or path.startswith("/api/v1/auth/resend-verification"):
            limit = settings.RATE_LIMIT_VERIFICATION_PER_HOUR
            window = 3600
            identifier = f"{base_id}:verification"
        else:
            identifier = f"{base_id}:default"

        is_allowed, remaining, reset_after = await self.rate_limit_service.check_rate_limit(
            identifier, limit, window
        )

        if not is_allowed:
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": reset_after,
                },
            )
        else:
            response = await call_next(request)

        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_after)
        if not is_allowed:
            response.headers["Retry-After"] = str(reset_after)

        return response
