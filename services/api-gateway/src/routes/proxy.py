import httpx
import structlog
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from src.config import settings

logger = structlog.get_logger(__name__)

router = APIRouter()

# Map URL prefixes to downstream service base URLs
SERVICE_MAP: dict[str, str] = {
    "/api/auth":                  settings.auth_service_url,
    "/api/plants":                settings.plant_service_url,
    "/api/compounds":             settings.plant_service_url,
    "/api/ethnobotanical":        settings.plant_service_url,
    "/api/genomic-data":          settings.plant_service_url,
    "/api/articles":              settings.plant_service_url,
    "/api/ontology-terms":        settings.plant_service_url,
    "/api/regional-availability": settings.plant_service_url,
    "/api/drug-references":       settings.plant_service_url,
    "/api/inference-jobs":        settings.plant_service_url,
    "/api/data-pipelines":        settings.plant_service_url,
    "/api/image-logs":            settings.plant_service_url,
    "/api/moderation":            settings.plant_service_url,
    "/api/query-logs":            settings.plant_service_url,
    "/api/analytics":             settings.plant_service_url,
    "/api/external-apis":         settings.plant_service_url,
    "/api/model-versions":        settings.plant_service_url,
    "/api/audit-log":             settings.auth_service_url,
    "/api/settings":              settings.auth_service_url,
    "/api/chatbot":               settings.chatbot_service_url,
    "/api/search":                settings.search_service_url,
    "/api/users":                 settings.user_service_url,
}


def _resolve_downstream(path: str) -> tuple[str, str] | None:
    """Return (base_url, downstream_path) for the first matching prefix."""
    for prefix, base_url in SERVICE_MAP.items():
        if path.startswith(prefix):
            downstream_path = path[len(prefix):] or "/"
            return base_url, downstream_path
    return None


def _build_headers(request: Request) -> dict[str, str]:
    """Forward relevant headers and inject authenticated user info."""
    headers: dict[str, str] = {}

    # Forward selected incoming headers
    for name in ("content-type", "accept", "accept-language", "x-request-id"):
        value = request.headers.get(name)
        if value:
            headers[name] = value

    # Inject user info set by AuthMiddleware
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        headers["X-User-Id"] = user_id
    user_role = getattr(request.state, "user_role", None)
    if user_role:
        headers["X-User-Role"] = user_role
    user_email = getattr(request.state, "user_email", None)
    if user_email:
        headers["X-User-Email"] = user_email

    return headers


@router.api_route(
    "/api/{service_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def proxy_request(request: Request, service_path: str):
    """Reverse-proxy incoming /api/* requests to the appropriate downstream service."""
    full_path = f"/api/{service_path}"
    resolved = _resolve_downstream(full_path)

    if resolved is None:
        logger.warning("no_matching_service", path=full_path)
        return StreamingResponse(
            iter([b'{"detail":"Service not found"}']),
            status_code=404,
            media_type="application/json",
        )

    base_url, downstream_path = resolved
    target_url = f"{base_url}{downstream_path}"

    # Preserve query string
    if request.url.query:
        target_url = f"{target_url}?{request.url.query}"

    headers = _build_headers(request)
    body = await request.body()

    logger.info(
        "proxy_request",
        method=request.method,
        path=full_path,
        target=target_url,
    )

    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            downstream_resp = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body if body else None,
            )
    except httpx.ConnectError:
        logger.error("downstream_unreachable", target=target_url)
        return StreamingResponse(
            iter([b'{"detail":"Downstream service unavailable"}']),
            status_code=502,
            media_type="application/json",
        )
    except httpx.TimeoutException:
        logger.error("downstream_timeout", target=target_url)
        return StreamingResponse(
            iter([b'{"detail":"Downstream service timed out"}']),
            status_code=504,
            media_type="application/json",
        )
    except Exception:
        logger.exception("proxy_error", target=target_url)
        return StreamingResponse(
            iter([b'{"detail":"Internal proxy error"}']),
            status_code=500,
            media_type="application/json",
        )

    # Build response headers, excluding hop-by-hop headers
    excluded = {"transfer-encoding", "content-encoding", "content-length", "connection"}
    resp_headers = {
        k: v
        for k, v in downstream_resp.headers.items()
        if k.lower() not in excluded
    }

    return StreamingResponse(
        iter([downstream_resp.content]),
        status_code=downstream_resp.status_code,
        headers=resp_headers,
        media_type=downstream_resp.headers.get("content-type", "application/json"),
    )
