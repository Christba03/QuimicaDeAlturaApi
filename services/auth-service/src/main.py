from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from redis.asyncio import from_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from starlette.middleware.base import BaseHTTPMiddleware

from src.config import settings
from src.api.v1.endpoints import auth, users, roles, verification, two_factor, password, sessions
from src.middleware.rate_limit import RateLimitMiddleware
from src.services.rate_limit_service import RateLimitService

logger = structlog.get_logger()

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG, pool_size=20, max_overflow=10)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("auth_service.starting", version=settings.APP_VERSION)
    # Store session factory on app state for access in dependencies
    app.state.db_session_factory = async_session_factory
    
    # Initialize Redis connection
    redis_client = from_url(settings.redis_url, decode_responses=False)
    app.state.redis = redis_client
    rate_limit_service = RateLimitService(redis_client)
    app.state.rate_limit_service = rate_limit_service
    
    # Initialize email queue service
    if settings.EMAIL_QUEUE_ENABLED:
        from src.services.email_queue import email_queue_service
        await email_queue_service.initialize()
        app.state.email_queue_service = email_queue_service
    
    yield
    
    # Cleanup
    if settings.EMAIL_QUEUE_ENABLED and hasattr(app.state, "email_queue_service"):
        await app.state.email_queue_service.close()
    await redis_client.aclose()
    logger.info("auth_service.shutting_down")
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    root_path="/auth",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiting middleware (accesses Redis from app.state at runtime)
class DynamicRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)
        
        if not hasattr(request.app.state, "rate_limit_service"):
            return await call_next(request)
        
        middleware = RateLimitMiddleware(request.app, request.app.state.rate_limit_service)
        return await middleware.dispatch(request, call_next)

app.add_middleware(DynamicRateLimitMiddleware)

# Prometheus metrics
Instrumentator().instrument(app).expose(app)

# Routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(verification.router, prefix="/api/v1/auth", tags=["Verification"])
app.include_router(two_factor.router, prefix="/api/v1/auth/2fa", tags=["Two-Factor Authentication"])
app.include_router(password.router, prefix="/api/v1/auth/password", tags=["Password"])
app.include_router(sessions.router, prefix="/api/v1/auth/sessions", tags=["Sessions"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(roles.router, prefix="/api/v1/roles", tags=["Roles"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "service": settings.APP_NAME, "version": settings.APP_VERSION}
