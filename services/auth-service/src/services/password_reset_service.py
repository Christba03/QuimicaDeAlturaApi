import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.models.verification_code import VerificationCodeType
from src.repositories.user_repository import UserRepository
from src.services.verification_service import VerificationService
from src.utils.password_validator import validate_password
from src.utils.security import hash_password

logger = structlog.get_logger()


class PasswordResetService:
    """Service for handling password reset operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.verification_service = VerificationService(session)

    async def request_password_reset(self, email: str) -> bool:
        """Request a password reset by sending a code to the user's email."""
        user = await self.user_repo.get_by_email(email)
        if user is None:
            # Don't reveal if email exists or not (security best practice)
            logger.info("password_reset.requested", email=email, user_found=False)
            return True

        # Generate and send reset code
        await self.verification_service.send_password_reset_code(
            user.id, user.email, user.first_name
        )

        logger.info("password_reset.requested", email=email, user_id=str(user.id))
        return True

    async def reset_password(self, email: str, code: str, new_password: str) -> bool:
        """Reset password using verification code."""
        user = await self.user_repo.get_by_email(email)
        if user is None:
            logger.warning("password_reset.user_not_found", email=email)
            return False

        # Verify the code
        if not await self.verification_service.verify_code(
            user.id, code, VerificationCodeType.PASSWORD_RESET
        ):
            logger.warning("password_reset.invalid_code", email=email, user_id=str(user.id))
            return False

        # Validate password strength
        validate_password(new_password)

        # Check password history
        new_password_hash = hash_password(new_password)
        if new_password_hash in user.password_history:
            logger.warning("password_reset.password_in_history", email=email, user_id=str(user.id))
            raise ValueError("Cannot reuse a recent password. Please choose a different password.")

        # Add current password to history
        if user.hashed_password:
            user.password_history.append(user.hashed_password)
        
        # Keep only last N passwords
        from src.config import settings
        if len(user.password_history) > settings.PASSWORD_HISTORY_SIZE:
            user.password_history = user.password_history[-settings.PASSWORD_HISTORY_SIZE:]

        # Update password
        user.hashed_password = new_password_hash
        await self.session.flush()

        # Invalidate all sessions (force re-login)
        from src.services.session_service import SessionService

        session_service = SessionService(self.session)
        await session_service.revoke_all_user_sessions(user.id)

        logger.info("password_reset.completed", email=email, user_id=str(user.id))
        return True
