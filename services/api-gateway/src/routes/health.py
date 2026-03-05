import httpx
import structlog
from fastapi import APIRouter

from src.config import settings

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["health"])

DOWNSTREAM_SERVICES = {
    "auth": settings.auth_service_url,
    "plant": settings.plant_service_url,
    "chatbot": settings.chatbot_service_url,
    "search": settings.search_service_url,
    "user": settings.user_service_url,
}


async def _check_service(name: str, base_url: str) -> dict:
    """Ping a downstream service's health endpoint."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{base_url}/health")
            return {
                "name": name,
                "status": "healthy" if resp.status_code == 200 else "unhealthy",
                "status_code": resp.status_code,
            }
    except httpx.ConnectError:
        return {"name": name, "status": "unreachable"}
    except Exception as exc:
        return {"name": name, "status": "error", "detail": str(exc)}


@router.get("/health")
async def health_check():
    """Basic liveness check for the API gateway itself."""
    return {"status": "healthy", "service": settings.service_name}


@router.get("/health/details")
async def health_check_detailed():
    """Deep health check that also probes every downstream service."""
    results = []
    for name, url in DOWNSTREAM_SERVICES.items():
        result = await _check_service(name, url)
        results.append(result)

    all_healthy = all(s["status"] == "healthy" for s in results)
    overall = "healthy" if all_healthy else "degraded"

    return {
        "status": overall,
        "service": settings.service_name,
        "dependencies": results,
    }
