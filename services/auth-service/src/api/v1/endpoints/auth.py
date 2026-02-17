from typing import AsyncGenerator

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.main import get_db
from src.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)
from src.schemas.user import UserResponse
from src.services.auth_service import AuthService

logger = structlog.get_logger()
router = APIRouter()


def get_auth_service(session: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(session)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Register a new user account."""
    try:
        user = await auth_service.register(
            email=payload.email,
            password=payload.password,
            first_name=payload.first_name,
            last_name=payload.last_name,
        )
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Authenticate user and return access and refresh tokens."""
    user = await auth_service.authenticate(email=payload.email, password=payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    tokens = await auth_service.create_tokens(user, ip_address=ip_address, user_agent=user_agent)
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    payload: RefreshTokenRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Refresh access token using a valid refresh token."""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    tokens = await auth_service.refresh_tokens(
        refresh_token=payload.refresh_token,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    if tokens is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    return tokens


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: LogoutRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Logout by revoking the refresh token."""
    await auth_service.logout(payload.refresh_token)
    return None
