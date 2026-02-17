import uuid
from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models.user import User
from src.repositories.user_repository import UserRepository
from src.services.session_service import SessionService
from src.utils.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

logger = structlog.get_logger()


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.session_service = SessionService(session)

    async def register(
        self, email: str, password: str, first_name: str, last_name: str
    ) -> User:
        """Register a new user."""
        if await self.user_repo.exists_by_email(email):
            raise ValueError("A user with this email already exists")

        user = User(
            email=email,
            hashed_password=hash_password(password),
            first_name=first_name,
            last_name=last_name,
        )
        user = await self.user_repo.create(user)
        logger.info("auth.user_registered", user_id=str(user.id), email=email)
        return user

    async def authenticate(self, email: str, password: str) -> User | None:
        """Authenticate user by email and password."""
        user = await self.user_repo.get_by_email(email)
        if user is None:
            return None
        if not verify_password(password, user.hashed_password):
            logger.warning("auth.failed_login_attempt", email=email)
            return None
        if not user.is_active:
            logger.warning("auth.inactive_user_login_attempt", email=email)
            return None
        return user

    async def create_tokens(
        self, user: User, ip_address: str | None = None, user_agent: str | None = None
    ) -> dict:
        """Create access and refresh tokens for the user."""
        role_names = [role.name for role in user.roles] if user.roles else []
        token_data = {"sub": str(user.id), "email": user.email, "roles": role_names}

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        await self.session_service.create_session(
            user_id=user.id,
            refresh_token=refresh_token,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        logger.info("auth.tokens_created", user_id=str(user.id))
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    async def refresh_tokens(
        self, refresh_token: str, ip_address: str | None = None, user_agent: str | None = None
    ) -> dict | None:
        """Refresh access token using a valid refresh token."""
        payload = decode_token(refresh_token)
        if payload is None or payload.get("type") != "refresh":
            return None

        session = await self.session_service.get_session_by_token(refresh_token)
        if session is None:
            return None

        user_id = uuid.UUID(payload["sub"])
        user = await self.user_repo.get_by_id(user_id)
        if user is None or not user.is_active:
            return None

        # Revoke old session and create new tokens
        await self.session_service.revoke_session(refresh_token)
        tokens = await self.create_tokens(user, ip_address=ip_address, user_agent=user_agent)

        logger.info("auth.tokens_refreshed", user_id=str(user_id))
        return tokens

    async def logout(self, refresh_token: str) -> bool:
        """Logout user by revoking their refresh token session."""
        revoked = await self.session_service.revoke_session(refresh_token)
        if revoked:
            logger.info("auth.user_logged_out")
        return revoked

    async def verify_access_token(self, token: str) -> dict | None:
        """Verify an access token and return its payload."""
        payload = decode_token(token)
        if payload is None or payload.get("type") != "access":
            return None
        return payload
