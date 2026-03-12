from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import get_settings
from src.dependencies import set_session_factory, set_redis_client
from src.api.v1.endpoints import plants, compounds, activities, articles, verification
from src.api.v1.endpoints import (
    ethnobotanical,
    genomic_data,
    ontology_terms,
    regional_availability,
    drug_references,
    inference_jobs,
    data_pipelines,
    image_logs,
    moderation,
    query_logs,
    analytics,
    external_apis,
    model_versions,
)

logger = structlog.get_logger()
settings = get_settings()

# Set by lifespan for health_check
redis_client: Redis | None = None

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    echo=settings.DEBUG,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client
    logger.info("starting_plant_service", port=settings.SERVICE_PORT)
    set_session_factory(async_session_factory)

    # Create all new tables (idempotent)
    from src.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Initialize Redis
    redis_client = None
    try:
        redis_client = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
        set_redis_client(redis_client)
        await redis_client.ping()
        logger.info("redis_connected")
    except Exception as exc:
        logger.warning("redis_connection_failed", error=str(exc))
        redis_client = None

    yield

    # Shutdown
    if redis_client:
        await redis_client.close()
    await engine.dispose()
    logger.info("plant_service_stopped")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Microservice for managing medicinal plant data, chemical compounds, and verification workflows.",
    lifespan=lifespan,
    root_path="/api/v1/plants",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# Routers
app.include_router(plants.router, prefix="/plants", tags=["Plants"])
app.include_router(compounds.router, prefix="/compounds", tags=["Compounds"])
app.include_router(activities.router, prefix="/activities", tags=["Activities"])
app.include_router(articles.router, prefix="/articles", tags=["Articles"])
app.include_router(
    verification.router, prefix="/verification", tags=["Verification"]
)
app.include_router(ethnobotanical.router,        prefix="/ethnobotanical",        tags=["Ethnobotanical"])
app.include_router(genomic_data.router,          prefix="/genomic-data",          tags=["Genomic Data"])
app.include_router(ontology_terms.router,        prefix="/ontology-terms",        tags=["Ontology Terms"])
app.include_router(regional_availability.router, prefix="/regional-availability", tags=["Regional Availability"])
app.include_router(drug_references.router,       prefix="/drug-references",       tags=["Drug References"])
app.include_router(inference_jobs.router,        prefix="/inference-jobs",        tags=["Inference Jobs"])
app.include_router(data_pipelines.router,        prefix="/data-pipelines",        tags=["Data Pipelines"])
app.include_router(image_logs.router,            prefix="/image-logs",            tags=["Image Logs"])
app.include_router(moderation.router,            prefix="/moderation",            tags=["Moderation"])
app.include_router(query_logs.router,            prefix="/query-logs",            tags=["Query Logs"])
app.include_router(analytics.router,             prefix="/analytics",             tags=["Analytics"])
app.include_router(external_apis.router,         prefix="/external-apis",         tags=["External APIs"])
app.include_router(model_versions.router,        prefix="/model-versions",        tags=["Model Versions"])


@app.get("/health", tags=["Health"])
async def health_check():
    checks = {"status": "healthy", "service": settings.APP_NAME}

    # Check database
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "connected"
    except Exception:
        checks["database"] = "disconnected"
        checks["status"] = "degraded"

    # Check Redis
    if redis_client:
        try:
            await redis_client.ping()
            checks["redis"] = "connected"
        except Exception:
            checks["redis"] = "disconnected"
            checks["status"] = "degraded"
    else:
        checks["redis"] = "not_configured"

    return checks


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.SERVICE_HOST,
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG,
    )
