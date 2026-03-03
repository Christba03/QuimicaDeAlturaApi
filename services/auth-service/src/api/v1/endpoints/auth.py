from datetime import timedelta
from typing import AsyncGenerator

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
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
from src.repositories.user_repository import UserRepository
from src.utils.password_validator import PasswordValidationError
from src.utils.security import create_access_token

logger = structlog.get_logger()
router = APIRouter()


class ChallengeTokenResponse(BaseModel):
    challenge_token: str
    requires_2fa: bool = True


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
    except PasswordValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=TokenResponse | ChallengeTokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Authenticate user and return access and refresh tokens, or 2FA challenge token."""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    user, requires_2fa = await auth_service.authenticate(
        email=payload.email, password=payload.password, ip_address=ip_address
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Check if device is trusted (skip 2FA for trusted devices)
    accept_language = request.headers.get("accept-language")
    from src.utils.device_fingerprint import generate_device_fingerprint
    from src.services.session_service import SessionService
    
    device_fingerprint = generate_device_fingerprint(
        user_agent=user_agent,
        ip_address=ip_address,
        accept_language=accept_language,
    )
    
    # If 2FA is enabled, check if device is trusted
    if requires_2fa:
        session_service = SessionService(auth_service.session)
        is_trusted = await session_service.is_device_trusted(user.id, device_fingerprint)
        
        if is_trusted:
            # Device is trusted, skip 2FA
            logger.info("login.trusted_device_skips_2fa", user_id=str(user.id), device_fingerprint=device_fingerprint[:16])
            tokens = await auth_service.create_tokens(
                user,
                ip_address=ip_address,
                user_agent=user_agent,
                accept_language=accept_language,
            )
            return tokens
        
        # Device not trusted, require 2FA
        if settings.REQUIRE_2FA_FOR_NEW_DEVICES:
            challenge_data = {
                "sub": str(user.id),
                "email": user.email,
                "type": "2fa_challenge",
                "ip_address": ip_address,
                "user_agent": user_agent,
            }
            challenge_token = create_access_token(challenge_data, expires_delta=timedelta(minutes=10))
            logger.info("login.2fa_challenge_required_new_device", user_id=str(user.id))
            return ChallengeTokenResponse(challenge_token=challenge_token, requires_2fa=True)

    # No 2FA required, issue tokens directly
    tokens = await auth_service.create_tokens(
        user,
        ip_address=ip_address,
        user_agent=user_agent,
        accept_language=accept_language,
    )
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


class ValidateTokenRequest(BaseModel):
    token: str


def get_user_repo(session: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(session)


@router.post("/validate", status_code=status.HTTP_200_OK)
async def validate_token(
    payload: ValidateTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Validate an access token and return user information (used by API gateway)."""
    token_payload = await auth_service.verify_access_token(payload.token)
    if token_payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = token_payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # Get user to fetch roles
    import uuid

    user = await user_repo.get_by_id(uuid.UUID(user_id))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Return user data for API gateway
    role_names = [role.name for role in user.roles] if user.roles else []
    primary_role = role_names[0] if role_names else None

    return {
        "user_id": str(user.id),
        "email": user.email,
        "role": primary_role,
        "roles": role_names,
    }
