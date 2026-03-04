import uuid
from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models.security_event import SecurityEventType
from src.models.user import User
from src.repositories.user_repository import UserRepository
from src.services.security_service import SecurityService
from src.services.session_service import SessionService
from src.services.verification_service import VerificationService
from src.utils.password_validator import PasswordValidationError, validate_password
from src.services.webhook_service import webhook_service
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
        self.verification_service = VerificationService(session)
        self.security_service = SecurityService(session)

    async def register(
        self, email: str, password: str, first_name: str, last_name: str
    ) -> User:
        """Register a new user and send verification email."""
        if await self.user_repo.exists_by_email(email):
            raise ValueError("A user with this email already exists")

        validate_password(password)

        user = User(
            email=email,
            hashed_password=hash_password(password),
            first_name=first_name,
            last_name=last_name,
            email_verified=False,
        )
        user = await self.user_repo.create(user)

        await self.verification_service.send_email_verification_code(user.id, email, first_name)
        await self.security_service.log_security_event(
            SecurityEventType.EMAIL_VERIFIED,
            user_id=user.id,
            metadata={"action": "registration"},
        )

        await webhook_service.emit("USER_REGISTERED", user_id=str(user.id), data={"email": email})
        logger.info("auth.user_registered", user_id=str(user.id), email=email)
        return user

    async def authenticate(
        self, email: str, password: str, ip_address: str | None = None
    ) -> tuple[User | None, bool]:
        """
        Authenticate user by email and password.
        Returns (user, requires_2fa). If user is None, authentication failed.
        """
        user = await self.user_repo.get_by_email(email)
        if user is None:
            return None, False

        if await self.security_service.check_account_locked(user):
            logger.warning("auth.account_locked", email=email, user_id=str(user.id))
            return None, False

        if not user.email_verified:
            logger.warning("auth.email_not_verified", email=email, user_id=str(user.id))
            return None, False

        if not verify_password(password, user.hashed_password):
            await self.security_service.handle_failed_login(user, ip_address)
            logger.warning("auth.failed_login_attempt", email=email, user_id=str(user.id))
            return None, False

        if not user.is_active:
            logger.warning("auth.inactive_user_login_attempt", email=email, user_id=str(user.id))
            return None, False

        await self.security_service.detect_suspicious_activity(user, ip_address)

        requires_2fa = user.two_factor_enabled
        if not requires_2fa:
            await self.security_service.handle_successful_login(user, ip_address)

        return user, requires_2fa

    async def create_tokens(
        self,
        user: User,
        ip_address: str | None = None,
        user_agent: str | None = None,
        accept_language: str | None = None,
        token_family: uuid.UUID | None = None,
    ) -> dict:
        """Create access and refresh tokens for the user."""
        role_names = [role.name for role in user.roles] if user.roles else []
        token_data = {"sub": str(user.id), "email": user.email, "roles": role_names}

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

        # Resolve GeoIP asynchronously (best-effort, non-blocking)
        geo = await self.security_service.resolve_geoip(ip_address)

        await self.session_service.create_session(
            user_id=user.id,
            refresh_token=refresh_token,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            accept_language=accept_language,
            token_family=token_family or uuid.uuid4(),
            country_code=geo.get("country_code"),
            country_name=geo.get("country_name"),
            region_name=geo.get("region_name"),
            city=geo.get("city"),
            latitude=geo.get("latitude"),
            longitude=geo.get("longitude"),
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
        """
        Refresh access token using a valid refresh token.
        Implements token family reuse detection: if a rotated token is replayed,
        the entire family is invalidated.
        """
        payload = decode_token(refresh_token)
        if payload is None or payload.get("type") != "refresh":
            return None

        # Check if the token exists (even if family-invalidated)
        session = await self.session_service.get_session_by_token_allow_invalidated(refresh_token)
        if session is None:
            return None

        # --- Reuse detection ---
        if session.family_invalidated:
            # A token from an already-rotated family was used — likely token theft.
            # Invalidate all remaining sessions in this family.
            logger.warning(
                "auth.refresh_token_reuse_detected",
                user_id=str(session.user_id),
                token_family=str(session.token_family),
            )
            await self.session_service.invalidate_token_family(session.token_family)
            await self.security_service.log_security_event(
                SecurityEventType.SUSPICIOUS_ACTIVITY,
                user_id=session.user_id,
                ip_address=ip_address,
                metadata={
                    "reason": "refresh_token_reuse",
                    "token_family": str(session.token_family),
                },
            )
            return None

        user_id = uuid.UUID(payload["sub"])
        user = await self.user_repo.get_by_id(user_id)
        if user is None or not user.is_active:
            return None

        # Revoke old session (mark family as used by deleting this session)
        await self.session_service.revoke_session(refresh_token)

        # Issue new tokens in the same family chain
        tokens = await self.create_tokens(
            user,
            ip_address=ip_address,
            user_agent=user_agent,
            accept_language=None,
            token_family=session.token_family,
        )

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

    async def update_password(self, user: User, new_password: str) -> None:
        """Update user password and invalidate all sessions."""
        validate_password(new_password)

        new_password_hash = hash_password(new_password)
        if new_password_hash in user.password_history:
            raise ValueError("Cannot reuse a recent password. Please choose a different password.")

        if user.hashed_password:
            user.password_history.append(user.hashed_password)

        if len(user.password_history) > settings.PASSWORD_HISTORY_SIZE:
            user.password_history = user.password_history[-settings.PASSWORD_HISTORY_SIZE:]

        user.hashed_password = new_password_hash
        await self.session.flush()

        await self.session_service.revoke_all_user_sessions(user.id)

        await self.security_service.log_security_event(
            SecurityEventType.PASSWORD_CHANGED,
            user_id=user.id,
        )

        await webhook_service.emit("PASSWORD_CHANGED", user_id=str(user.id))
        logger.info("auth.password_updated", user_id=str(user.id))
