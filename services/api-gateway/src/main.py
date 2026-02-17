import structlog
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from src.config import settings
from src.middleware.auth import AuthMiddleware
from src.middleware.cors import setup_cors
from src.middleware.rate_limit import RateLimitMiddleware
from src.routes import health, proxy

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer() if settings.debug else structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(0),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

app = FastAPI(
    title="Quimica De Altura - API Gateway",
    description="Central API gateway that routes requests to downstream microservices.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# --- Middleware (order matters: outermost runs first) ---
# CORS must be the outermost middleware so preflight responses include the right headers.
setup_cors(app, settings.cors_origins_list)

# Rate limiting sits before auth so abusive unauthenticated traffic is blocked early.
app.add_middleware(RateLimitMiddleware)

# Auth middleware validates JWTs and injects user info into request state.
app.add_middleware(AuthMiddleware)

# --- Prometheus metrics ---
Instrumentator().instrument(app).expose(app)

# --- Routers ---
app.include_router(health.router)
app.include_router(proxy.router)


@app.on_event("startup")
async def on_startup():
    logger.info("gateway_started", service=settings.service_name, debug=settings.debug)


@app.on_event("shutdown")
async def on_shutdown():
    logger.info("gateway_stopped", service=settings.service_name)
