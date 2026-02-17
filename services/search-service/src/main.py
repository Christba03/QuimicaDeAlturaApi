from contextlib import asynccontextmanager
from typing import AsyncIterator

import structlog
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from src.config import settings
from src.core.elasticsearch_client import (
    close_client,
    create_client,
    ensure_indices,
    health_check,
)
from src.api.v1.endpoints import search, autocomplete, recommendations

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Manage startup / shutdown of shared resources."""
    logger.info("search_service_starting", version=settings.SERVICE_VERSION)
    await create_client()
    try:
        await ensure_indices()
    except Exception as exc:
        logger.warning("index_setup_skipped", reason=str(exc))
    yield
    await close_client()
    logger.info("search_service_stopped")


app = FastAPI(
    title="Quimica de Altura - Search Service",
    description="Full-text search over medicinal plants, compounds, and biological activities using Elasticsearch.",
    version=settings.SERVICE_VERSION,
    lifespan=lifespan,
)

# Prometheus instrumentation
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# Register routers
app.include_router(
    search.router,
    prefix="/api/v1/search",
    tags=["search"],
)
app.include_router(
    autocomplete.router,
    prefix="/api/v1/autocomplete",
    tags=["autocomplete"],
)
app.include_router(
    recommendations.router,
    prefix="/api/v1/recommendations",
    tags=["recommendations"],
)


# ------------------------------------------------------------------
# Health endpoints
# ------------------------------------------------------------------


@app.get("/health", tags=["health"])
async def health():
    es_health = await health_check()
    healthy = es_health.get("status") in ("green", "yellow")
    return {
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "status": "healthy" if healthy else "degraded",
        "elasticsearch": es_health,
    }


@app.get("/health/live", tags=["health"])
async def liveness():
    return {"status": "alive"}


@app.get("/health/ready", tags=["health"])
async def readiness():
    es_health = await health_check()
    ready = es_health.get("status") in ("green", "yellow")
    return {"status": "ready" if ready else "not_ready", "elasticsearch": es_health}
