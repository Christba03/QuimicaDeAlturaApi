"""
ABAC policy management endpoints.
Admin-only: create, list, delete, and evaluate policies.
"""
import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies import require_superuser
from src.main import get_db
from src.services.policy_service import PolicyService

logger = structlog.get_logger()
router = APIRouter()


class PolicyCreate(BaseModel):
    subject_type: str       # "user" | "role"
    subject_id: str         # UUID string or role name; "*" = all
    resource: str           # resource type or "*"
    action: str             # action or "*"
    effect: str = "allow"   # "allow" | "deny"
    conditions: dict | None = None


class PolicyResponse(BaseModel):
    id: uuid.UUID
    subject_type: str
    subject_id: str
    resource: str
    action: str
    effect: str
    conditions: dict | None
    is_active: bool

    model_config = {"from_attributes": True}


class PolicyEvaluateRequest(BaseModel):
    user_id: uuid.UUID
    user_roles: list[str] = []
    action: str
    resource: str
    context: dict | None = None


class PolicyEvaluateResponse(BaseModel):
    allowed: bool
    user_id: uuid.UUID
    action: str
    resource: str


def get_policy_service(session: AsyncSession = Depends(get_db)) -> PolicyService:
    return PolicyService(session)


@router.post("/", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_policy(
    payload: PolicyCreate,
    _: dict = Depends(require_superuser),
    svc: PolicyService = Depends(get_policy_service),
):
    """Create a new ABAC policy."""
    if payload.effect not in ("allow", "deny"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="effect must be 'allow' or 'deny'")
    policy = await svc.create_policy(
        subject_type=payload.subject_type,
        subject_id=payload.subject_id,
        resource=payload.resource,
        action=payload.action,
        effect=payload.effect,
        conditions=payload.conditions,
    )
    return policy


@router.get("/", response_model=list[PolicyResponse])
async def list_policies(
    subject_type: str | None = Query(None),
    resource: str | None = Query(None),
    _: dict = Depends(require_superuser),
    svc: PolicyService = Depends(get_policy_service),
):
    """List active ABAC policies."""
    return await svc.list_policies(subject_type=subject_type, resource=resource)


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(
    policy_id: uuid.UUID,
    _: dict = Depends(require_superuser),
    svc: PolicyService = Depends(get_policy_service),
):
    """Delete an ABAC policy."""
    deleted = await svc.delete_policy(policy_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    return None


@router.post("/evaluate", response_model=PolicyEvaluateResponse)
async def evaluate_policy(
    payload: PolicyEvaluateRequest,
    _: dict = Depends(require_superuser),
    svc: PolicyService = Depends(get_policy_service),
):
    """
    Evaluate whether a user is allowed to perform an action on a resource.
    Useful for debugging and gateway pre-checks.
    """
    allowed = await svc.is_allowed(
        user_id=payload.user_id,
        user_roles=payload.user_roles,
        action=payload.action,
        resource=payload.resource,
        context=payload.context,
    )
    return PolicyEvaluateResponse(
        allowed=allowed,
        user_id=payload.user_id,
        action=payload.action,
        resource=payload.resource,
    )
