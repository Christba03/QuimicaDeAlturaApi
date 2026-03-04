"""
Kubernetes-ready health and readiness probe endpoints.

  GET /healthz  — liveness probe: service is running
  GET /readyz   — readiness probe: DB + Redis are reachable
"""
import structlog
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

logger = structlog.get_logger()
router = APIRouter()


@router.get("/healthz", tags=["Health"])
async def liveness():
    """Liveness probe — always returns 200 if the process is running."""
    return {"status": "alive"}


@router.get("/readyz", tags=["Health"])
async def readiness(request: Request):
    """
    Readiness probe — checks DB connection pool and Redis connectivity.
    Returns 200 when all dependencies are healthy, 503 otherwise.
    """
    checks: dict[str, str] = {}
    healthy = True

    # --- Database check ---
    try:
        db_factory = request.app.state.db_session_factory
        async with db_factory() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"
        healthy = False
        logger.error("readyz.db_check_failed", error=str(e))

    # --- Redis check ---
    try:
        redis = request.app.state.redis
        await redis.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"
        healthy = False
        logger.error("readyz.redis_check_failed", error=str(e))

    http_status = status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(
        status_code=http_status,
        content={"status": "ready" if healthy else "not_ready", "checks": checks},
    )
