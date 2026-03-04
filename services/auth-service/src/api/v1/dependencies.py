"""
Shared FastAPI dependencies for authentication and authorization.
"""
import structlog
from fastapi import Depends, Header, HTTPException, Request, status

from src.utils.security import decode_token, is_token_blacklisted

logger = structlog.get_logger()


async def get_current_user(
    request: Request,
    authorization: str = Header(None),
) -> dict:
    """
    Validate the Bearer token from the Authorization header.
    Checks JWT signature, token type, and Redis blacklist.
    Returns the decoded token payload on success.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization[len("Bearer "):]
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    redis_client = request.app.state.redis
    if await is_token_blacklisted(redis_client, payload):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


async def require_superuser(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Require the authenticated user to have admin role or is_superuser flag.
    Uses token payload to avoid a DB lookup.
    """
    roles = current_user.get("roles", [])
    if "admin" not in roles and not current_user.get("is_superuser"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
