import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.main import get_db
from src.models.role import Permission, Role

logger = structlog.get_logger()
router = APIRouter()


# Request / Response schemas (local to this module)
class RoleCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: str | None = Field(None, max_length=255)
    permission_ids: list[uuid.UUID] = Field(default_factory=list)


class RoleUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=50)
    description: str | None = Field(None, max_length=255)
    permission_ids: list[uuid.UUID] | None = None


class PermissionResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None

    model_config = {"from_attributes": True}


class RoleDetailResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    permissions: list[PermissionResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class RoleListResponse(BaseModel):
    roles: list[RoleDetailResponse]
    total: int


# ---- Endpoints ----

@router.get("/", response_model=RoleListResponse)
async def list_roles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
):
    """List all roles with pagination."""
    count_stmt = select(func.count()).select_from(Role)
    total = (await session.execute(count_stmt)).scalar_one()

    offset = (page - 1) * page_size
    stmt = (
        select(Role)
        .options(selectinload(Role.permissions))
        .order_by(Role.name)
        .offset(offset)
        .limit(page_size)
    )
    result = await session.execute(stmt)
    roles = list(result.scalars().all())
    return RoleListResponse(roles=roles, total=total)


@router.get("/{role_id}", response_model=RoleDetailResponse)
async def get_role(role_id: uuid.UUID, session: AsyncSession = Depends(get_db)):
    """Get a specific role by ID."""
    stmt = select(Role).options(selectinload(Role.permissions)).where(Role.id == role_id)
    result = await session.execute(stmt)
    role = result.scalar_one_or_none()
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return role


@router.post("/", response_model=RoleDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_role(payload: RoleCreateRequest, session: AsyncSession = Depends(get_db)):
    """Create a new role."""
    # Check for duplicate name
    exists_stmt = select(func.count()).select_from(Role).where(Role.name == payload.name)
    if (await session.execute(exists_stmt)).scalar_one() > 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role name already exists")

    role = Role(name=payload.name, description=payload.description)

    if payload.permission_ids:
        perm_stmt = select(Permission).where(Permission.id.in_(payload.permission_ids))
        perms = list((await session.execute(perm_stmt)).scalars().all())
        role.permissions = perms

    session.add(role)
    await session.flush()
    await session.refresh(role, attribute_names=["permissions"])
    return role


@router.put("/{role_id}", response_model=RoleDetailResponse)
async def update_role(
    role_id: uuid.UUID,
    payload: RoleUpdateRequest,
    session: AsyncSession = Depends(get_db),
):
    """Update an existing role."""
    stmt = select(Role).options(selectinload(Role.permissions)).where(Role.id == role_id)
    result = await session.execute(stmt)
    role = result.scalar_one_or_none()
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    if payload.name is not None:
        role.name = payload.name
    if payload.description is not None:
        role.description = payload.description
    if payload.permission_ids is not None:
        perm_stmt = select(Permission).where(Permission.id.in_(payload.permission_ids))
        perms = list((await session.execute(perm_stmt)).scalars().all())
        role.permissions = perms

    await session.flush()
    await session.refresh(role, attribute_names=["permissions"])
    return role


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(role_id: uuid.UUID, session: AsyncSession = Depends(get_db)):
    """Delete a role."""
    stmt = select(Role).where(Role.id == role_id)
    result = await session.execute(stmt)
    role = result.scalar_one_or_none()
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    await session.delete(role)
    await session.flush()
    return None
