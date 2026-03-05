import httpx
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.config import settings

logger = structlog.get_logger(__name__)

# Paths that do not require authentication
PUBLIC_PATHS = {
    "/health",
    "/metrics",
    "/docs",
    "/openapi.json",
    "/redoc",
}


class AuthMiddleware(BaseHTTPMiddleware):
    """Validates JWT tokens by calling the auth service and injects user info into request headers."""

    async def dispatch(self, request: Request, call_next):
        # Skip authentication for public paths and all auth-service routes
        # (auth-service manages its own authentication internally)
        if (
            request.url.path in PUBLIC_PATHS
            or request.url.path.startswith("/health")
            or request.url.path.startswith("/api/auth/")
        ):
            return await call_next(request)

        # Allow preflight CORS requests through
        if request.method == "OPTIONS":
            return await call_next(request)

        authorization = request.headers.get("Authorization")
        if not authorization:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing Authorization header"},
            )

        if not authorization.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Authorization header must use Bearer scheme"},
            )

        token = authorization[len("Bearer "):]

        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
                response = await client.post(
                    f"{settings.auth_service_url}/auth/validate",
                    json={"token": token},
                )

            if response.status_code != 200:
                logger.warning("auth_validation_failed", status=response.status_code)
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid or expired token"},
                )

            user_data = response.json()
            user_id = str(user_data.get("user_id", ""))
            user_role = user_data.get("role", "")
            user_email = user_data.get("email", "")

        except httpx.ConnectError:
            logger.error("auth_service_unreachable")
            return JSONResponse(
                status_code=503,
                content={"detail": "Authentication service unavailable"},
            )
        except Exception:
            logger.exception("auth_validation_error")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal authentication error"},
            )

        # Inject validated user information into request state so downstream
        # handlers and the proxy can forward them as headers.
        request.state.user_id = user_id
        request.state.user_role = user_role
        request.state.user_email = user_email

        response = await call_next(request)
        return response
