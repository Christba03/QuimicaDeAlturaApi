from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from redis.asyncio import from_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from starlette.middleware.base import BaseHTTPMiddleware

from src.config import settings
from src.dependencies import set_session_factory
from src.api.v1.endpoints import auth, users, roles, verification, two_factor, password, sessions
from src.api.v1.endpoints import oauth, api_keys, policies, audit
from src.api.v1.endpoints import settings as settings_router, audit_log
from src.api.v1.endpoints.health import router as health_router
from src.middleware.rate_limit import RateLimitMiddleware
from src.services.rate_limit_service import RateLimitService

logger = structlog.get_logger()

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG, pool_size=20, max_overflow=10)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def _setup_opentelemetry(app: FastAPI) -> None:
    """Configure OpenTelemetry tracing if enabled."""
    if not settings.OTEL_ENABLED:
        return
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource

        resource = Resource(attributes={"service.name": settings.OTEL_SERVICE_NAME})
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
        logger.info("otel.initialized", endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT)
    except ImportError:
        logger.warning("otel.not_available", reason="opentelemetry packages not installed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("auth_service.starting", version=settings.APP_VERSION)
    set_session_factory(async_session_factory)
    app.state.db_session_factory = async_session_factory

    # Create new tables (idempotent)
    from src.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Redis
    redis_client = from_url(settings.redis_url, decode_responses=False)
    app.state.redis = redis_client
    rate_limit_service = RateLimitService(redis_client)
    app.state.rate_limit_service = rate_limit_service

    # Email queue
    if settings.EMAIL_QUEUE_ENABLED:
        from src.services.email_queue import email_queue_service
        await email_queue_service.initialize()
        app.state.email_queue_service = email_queue_service

    # Webhook pub-sub service
    if settings.WEBHOOK_ENABLED:
        from src.services.webhook_service import webhook_service
        webhook_service.initialize(redis_client)
        logger.info("webhook_service.initialized", channel=settings.WEBHOOK_REDIS_CHANNEL)

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

# OpenTelemetry (must be configured before middleware/routes)
_setup_opentelemetry(app)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Rate Limiting middleware
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

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

# Core auth
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(verification.router, prefix="/api/v1/auth", tags=["Verification"])
app.include_router(two_factor.router, prefix="/api/v1/auth/2fa", tags=["Two-Factor Authentication"])
app.include_router(password.router, prefix="/api/v1/auth/password", tags=["Password"])
app.include_router(sessions.router, prefix="/api/v1/auth/sessions", tags=["Sessions"])

# OAuth 2.0 social login
app.include_router(oauth.router, prefix="/api/v1/auth/oauth", tags=["OAuth"])

# User & role management
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(roles.router, prefix="/api/v1/roles", tags=["Roles"])

# API Keys
app.include_router(api_keys.router, prefix="/api/v1", tags=["API Keys"])

# ABAC Policies
app.include_router(policies.router, prefix="/api/v1/policies", tags=["Policies"])

# Audit log (internal)
app.include_router(audit.router, prefix="/api/v1/audit", tags=["Audit"])

# Dashboard endpoints (routed via gateway /api/settings and /api/audit-log)
app.include_router(settings_router.router, prefix="/api/v1/settings", tags=["Settings"])
app.include_router(audit_log.router,       prefix="/api/v1/audit-log",  tags=["Audit Log"])

# Health & readiness probes (registered at root, no /auth prefix via root_path)
app.include_router(health_router, tags=["Health"])


@app.get("/health", tags=["Health"])
async def health_check():
    """Legacy health endpoint — use /healthz and /readyz for probes."""
    return {"status": "healthy", "service": settings.APP_NAME, "version": settings.APP_VERSION}
