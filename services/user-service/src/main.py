from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import redis.asyncio as aioredis

from src.config import get_settings
from src.dependencies import set_session_factory, set_redis_client
from src.api.v1.endpoints import profile, favorites, usage_reports, history

logger = structlog.get_logger(__name__)
settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

redis_client: aioredis.Redis | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client
    logger.info("Starting User Service", port=settings.PORT)

    set_session_factory(async_session)

    redis_client = aioredis.from_url(
        settings.redis_url,
        decode_responses=True,
    )
    await redis_client.ping()
    set_redis_client(redis_client)
    logger.info("Redis connection established")

    yield

    if redis_client:
        await redis_client.close()
    await engine.dispose()
    logger.info("User Service shut down")


app = FastAPI(
    title="QuimicaDeAltura - User Service",
    description="Manages user profiles, favorites, usage reports, and browsing history for medicinal plants.",
    version="1.0.0",
    lifespan=lifespan,
    root_path="/api/v1/users",
)

Instrumentator().instrument(app).expose(app)

app.include_router(profile.router, prefix="/profile", tags=["Profile"])
app.include_router(favorites.router, prefix="/favorites", tags=["Favorites"])
app.include_router(usage_reports.router, prefix="/usage-reports", tags=["Usage Reports"])
app.include_router(history.router, prefix="/history", tags=["History"])


@app.get("/health", tags=["Health"])
async def health_check():
    checks = {"status": "healthy", "service": settings.SERVICE_NAME}
    try:
        async with engine.connect() as conn:
            await conn.execute(
                __import__("sqlalchemy").text("SELECT 1")
            )
        checks["database"] = "connected"
    except Exception as exc:
        checks["database"] = f"error: {exc}"
        checks["status"] = "degraded"

    try:
        if redis_client:
            await redis_client.ping()
        checks["redis"] = "connected"
    except Exception as exc:
        checks["redis"] = f"error: {exc}"
        checks["status"] = "degraded"

    return checks
