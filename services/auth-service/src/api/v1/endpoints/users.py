import uuid
from datetime import datetime, timezone
from typing import Literal

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies import require_superuser
from src.main import get_db
from src.models.user import User
from src.models.role import Role
from src.repositories.user_repository import UserRepository
from src.schemas.user import UserCreate, UserListResponse, UserResponse, UserUpdate
from src.services.session_service import SessionService
from src.utils.security import hash_password

logger = structlog.get_logger()
router = APIRouter()


def get_user_repo(session: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(session)


def get_db_session(session: AsyncSession = Depends(get_db)) -> AsyncSession:
    return session


# ---------------------------------------------------------------------------
# Standard CRUD
# ---------------------------------------------------------------------------


@router.get("/", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    # Admin filters
    status: Literal["active", "inactive", "locked", "all"] | None = Query(None),
    verified: bool | None = Query(None, description="Filter by email verification status"),
    role: str | None = Query(None, description="Filter by role name"),
    _: dict = Depends(require_superuser),
    repo: UserRepository = Depends(get_user_repo),
    session: AsyncSession = Depends(get_db_session),
):
    """
    List users with pagination and admin filters.
    - ?status=locked  → accounts with active lockout
    - ?verified=false → unverified email accounts
    - ?role=analyst   → users with a specific role
    """
    if status is None and verified is None and role is None:
        # Fast path: no filters
        users, total = await repo.list_users(page=page, page_size=page_size)
        return UserListResponse(users=users, total=total, page=page, page_size=page_size)

    # Build filtered query
    stmt = select(User)
    count_stmt = select(func.count()).select_from(User)

    now = datetime.now(timezone.utc)

    if status == "locked":
        stmt = stmt.where(User.locked_until > now)
        count_stmt = count_stmt.where(User.locked_until > now)
    elif status == "active":
        stmt = stmt.where(User.is_active == True)
        count_stmt = count_stmt.where(User.is_active == True)
    elif status == "inactive":
        stmt = stmt.where(User.is_active == False)
        count_stmt = count_stmt.where(User.is_active == False)

    if verified is not None:
        stmt = stmt.where(User.email_verified == verified)
        count_stmt = count_stmt.where(User.email_verified == verified)

    if role is not None:
        stmt = stmt.join(User.roles).where(Role.name == role)
        count_stmt = count_stmt.join(User.roles).where(Role.name == role)

    total_result = await session.execute(count_stmt)
    total = total_result.scalar_one()

    stmt = stmt.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(stmt)
    users = list(result.scalars().all())

    return UserListResponse(users=users, total=total, page=page, page_size=page_size)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    _: dict = Depends(require_superuser),
    repo: UserRepository = Depends(get_user_repo),
):
    """Get a specific user by ID."""
    user = await repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    _: dict = Depends(require_superuser),
    repo: UserRepository = Depends(get_user_repo),
):
    """Create a new user (admin operation)."""
    if await repo.exists_by_email(payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        is_active=payload.is_active,
        is_superuser=payload.is_superuser,
    )
    user = await repo.create(user)

    if payload.role_ids:
        await repo.update(user, {"role_ids": payload.role_ids})

    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    _: dict = Depends(require_superuser),
    repo: UserRepository = Depends(get_user_repo),
):
    """Update an existing user."""
    user = await repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    update_data = payload.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["hashed_password"] = hash_password(update_data.pop("password"))

    return await repo.update(user, update_data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    _: dict = Depends(require_superuser),
    repo: UserRepository = Depends(get_user_repo),
):
    """Delete a user."""
    user = await repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await repo.delete(user)
    return None


# ---------------------------------------------------------------------------
# Admin actions
# ---------------------------------------------------------------------------


@router.post("/{user_id}/unlock", status_code=status.HTTP_200_OK)
async def unlock_user(
    user_id: uuid.UUID,
    _: dict = Depends(require_superuser),
    repo: UserRepository = Depends(get_user_repo),
):
    """Unlock a locked user account (admin action)."""
    user = await repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.locked_until is None or user.locked_until <= datetime.now(timezone.utc):
        return {"message": "Account is not locked", "user_id": str(user_id)}
    user.locked_until = None
    user.failed_login_attempts = 0
    await repo.session.flush()
    logger.info("admin.user_unlocked", user_id=str(user_id))
    return {"message": "Account unlocked", "user_id": str(user_id)}


@router.post("/{user_id}/force-logout", status_code=status.HTTP_200_OK)
async def force_logout_user(
    user_id: uuid.UUID,
    _: dict = Depends(require_superuser),
    repo: UserRepository = Depends(get_user_repo),
):
    """Revoke all sessions for a user (admin force-logout)."""
    user = await repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    session_svc = SessionService(repo.session)
    count = await session_svc.revoke_all_user_sessions(user_id)
    logger.info("admin.force_logout", user_id=str(user_id), sessions_revoked=count)
    return {"message": f"Revoked {count} session(s)", "user_id": str(user_id)}


# ---------------------------------------------------------------------------
# Bulk operations
# ---------------------------------------------------------------------------


class BulkActionRequest(BaseModel):
    user_ids: list[uuid.UUID]
    action: Literal["activate", "deactivate", "delete", "unlock"]


class BulkActionResponse(BaseModel):
    action: str
    affected: int
    user_ids: list[str]


@router.post("/bulk-action", response_model=BulkActionResponse)
async def bulk_user_action(
    payload: BulkActionRequest,
    _: dict = Depends(require_superuser),
    repo: UserRepository = Depends(get_user_repo),
):
    """
    Apply a bulk action to multiple users.
    Actions: activate | deactivate | delete | unlock
    """
    if not payload.user_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No user IDs provided")
    if len(payload.user_ids) > 500:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximum 500 users per bulk action")

    affected_ids: list[str] = []
    now = datetime.now(timezone.utc)

    for uid in payload.user_ids:
        user = await repo.get_by_id(uid)
        if user is None:
            continue

        if payload.action == "activate":
            user.is_active = True
        elif payload.action == "deactivate":
            user.is_active = False
        elif payload.action == "delete":
            await repo.delete(user)
        elif payload.action == "unlock":
            user.locked_until = None
            user.failed_login_attempts = 0

        affected_ids.append(str(uid))

    await repo.session.flush()
    logger.info("admin.bulk_action", action=payload.action, affected=len(affected_ids))

    return BulkActionResponse(action=payload.action, affected=len(affected_ids), user_ids=affected_ids)
