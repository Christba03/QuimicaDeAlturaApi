"""
API Key management endpoints.
Users can create, list, and revoke their own API keys.
The validate endpoint is for services/gateways to verify a raw key.
"""
import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies import get_current_user
from src.dependencies import get_db
from src.schemas.api_key import (
    APIKeyCreate,
    APIKeyCreatedResponse,
    APIKeyResponse,
    APIKeyValidateRequest,
    APIKeyValidateResponse,
)
from src.services.api_key_service import APIKeyService

logger = structlog.get_logger()
router = APIRouter()


def get_api_key_service(session: AsyncSession = Depends(get_db)) -> APIKeyService:
    return APIKeyService(session)


@router.post(
    "/users/{user_id}/api-keys",
    response_model=APIKeyCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["API Keys"],
)
async def create_api_key(
    user_id: uuid.UUID,
    payload: APIKeyCreate,
    current_user: dict = Depends(get_current_user),
    svc: APIKeyService = Depends(get_api_key_service),
):
    """
    Create a new API key for a user.
    **The plaintext key is returned only once — store it securely.**
    """
    if str(user_id) != current_user.get("sub"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    api_key, raw_key = await svc.create_key(
        user_id=user_id,
        name=payload.name,
        scopes=payload.scopes,
        expires_at=payload.expires_at,
    )
    return APIKeyCreatedResponse(
        id=api_key.id,
        name=api_key.name,
        key=raw_key,
        key_prefix=api_key.key_prefix,
        scopes=api_key.scopes,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
    )


@router.get(
    "/users/{user_id}/api-keys",
    response_model=list[APIKeyResponse],
    tags=["API Keys"],
)
async def list_api_keys(
    user_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    svc: APIKeyService = Depends(get_api_key_service),
):
    """List all API keys for a user (no plaintext keys returned)."""
    if str(user_id) != current_user.get("sub"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return await svc.list_keys(user_id)


@router.delete(
    "/users/{user_id}/api-keys/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["API Keys"],
)
async def revoke_api_key(
    user_id: uuid.UUID,
    key_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    svc: APIKeyService = Depends(get_api_key_service),
):
    """Revoke (deactivate) an API key."""
    if str(user_id) != current_user.get("sub"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    revoked = await svc.revoke_key(key_id=key_id, user_id=user_id)
    if not revoked:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    return None


@router.post(
    "/api-keys/validate",
    response_model=APIKeyValidateResponse,
    tags=["API Keys"],
)
async def validate_api_key(
    payload: APIKeyValidateRequest,
    svc: APIKeyService = Depends(get_api_key_service),
):
    """
    Validate a raw API key string (used by API gateway).
    Returns user_id + scopes if valid.
    """
    api_key = await svc.validate_key(payload.key)
    if api_key is None:
        return APIKeyValidateResponse(valid=False)
    return APIKeyValidateResponse(valid=True, user_id=api_key.user_id, scopes=api_key.scopes)
