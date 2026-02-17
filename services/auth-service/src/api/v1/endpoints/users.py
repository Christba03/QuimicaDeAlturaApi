import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.main import get_db
from src.models.role import Role
from src.repositories.user_repository import UserRepository
from src.schemas.user import UserCreate, UserListResponse, UserResponse, UserUpdate
from src.utils.security import hash_password

logger = structlog.get_logger()
router = APIRouter()


def get_user_repo(session: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(session)


@router.get("/", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    repo: UserRepository = Depends(get_user_repo),
):
    """List all users with pagination."""
    users, total = await repo.list_users(page=page, page_size=page_size)
    return UserListResponse(users=users, total=total, page=page, page_size=page_size)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
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
    repo: UserRepository = Depends(get_user_repo),
):
    """Create a new user (admin operation)."""
    if await repo.exists_by_email(payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    from src.models.user import User

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
    repo: UserRepository = Depends(get_user_repo),
):
    """Update an existing user."""
    user = await repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    update_data = payload.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["hashed_password"] = hash_password(update_data.pop("password"))

    user = await repo.update(user, update_data)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    repo: UserRepository = Depends(get_user_repo),
):
    """Delete a user."""
    user = await repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await repo.delete(user)
    return None
