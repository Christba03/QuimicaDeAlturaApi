import secrets
import uuid
from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models.verification_code import VerificationCode, VerificationCodeType
from src.services.email_queue import email_queue_service
from src.services.email_service import email_service
from src.utils.security import hash_password, verify_password

logger = structlog.get_logger()


class VerificationService:
    """Service for handling email verification and password reset codes."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _generate_code(self) -> str:
        """Generate a 6-digit verification code."""
        return f"{secrets.randbelow(900000) + 100000:06d}"

    async def create_verification_code(
        self, user_id: uuid.UUID, code_type: VerificationCodeType
    ) -> tuple[str, VerificationCode]:
        """Create a new verification code and return both plaintext and hashed versions."""
        code = self._generate_code()
        code_hash = hash_password(code)

        # Determine expiry based on code type
        if code_type == VerificationCodeType.EMAIL_VERIFICATION:
            expiry_minutes = settings.EMAIL_VERIFICATION_CODE_EXPIRY_MINUTES
        elif code_type == VerificationCodeType.PASSWORD_RESET:
            expiry_minutes = settings.PASSWORD_RESET_CODE_EXPIRY_MINUTES
        else:  # TWO_FACTOR_EMAIL
            expiry_minutes = 10

        expires_at = datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes)

        verification_code = VerificationCode(
            user_id=user_id,
            code_hash=code_hash,
            code_type=code_type,
            expires_at=expires_at,
        )

        self.session.add(verification_code)
        await self.session.flush()

        logger.info(
            "verification_code.created",
            user_id=str(user_id),
            code_type=code_type.value,
            expires_at=expires_at.isoformat(),
        )

        return code, verification_code

    async def verify_code(
        self, user_id: uuid.UUID, code: str, code_type: VerificationCodeType
    ) -> bool:
        """Verify a code and mark it as used."""
        # Get all valid (non-expired, unused) codes for this user and type
        stmt = select(VerificationCode).where(
            VerificationCode.user_id == user_id,
            VerificationCode.code_type == code_type,
            VerificationCode.expires_at > datetime.now(timezone.utc),
            VerificationCode.used_at.is_(None),
        )

        result = await self.session.execute(stmt)
        codes = result.scalars().all()

        # Try to match the code against any valid code
        for verification_code in codes:
            if verify_password(code, verification_code.code_hash):
                # Mark as used
                verification_code.used_at = datetime.now(timezone.utc)
                await self.session.flush()

                logger.info(
                    "verification_code.verified",
                    user_id=str(user_id),
                    code_type=code_type.value,
                    code_id=str(verification_code.id),
                )
                return True

        logger.warning(
            "verification_code.invalid",
            user_id=str(user_id),
            code_type=code_type.value,
        )
        return False

    async def send_email_verification_code(self, user_id: uuid.UUID, email: str, first_name: str | None = None) -> str:
        """Create and send email verification code."""
        code, _ = await self.create_verification_code(user_id, VerificationCodeType.EMAIL_VERIFICATION)
        if settings.EMAIL_QUEUE_ENABLED:
            await email_queue_service.enqueue_verification_email(email, code, first_name)
        else:
            await email_service.send_verification_email(email, code, first_name)
        return code

    async def send_password_reset_code(self, user_id: uuid.UUID, email: str, first_name: str | None = None) -> str:
        """Create and send password reset code."""
        code, _ = await self.create_verification_code(user_id, VerificationCodeType.PASSWORD_RESET)
        if settings.EMAIL_QUEUE_ENABLED:
            await email_queue_service.enqueue_password_reset_email(email, code, first_name)
        else:
            await email_service.send_password_reset_email(email, code, first_name)
        return code

    async def send_two_factor_email_code(self, user_id: uuid.UUID, email: str, first_name: str | None = None) -> str:
        """Create and send 2FA email code."""
        code, _ = await self.create_verification_code(user_id, VerificationCodeType.TWO_FACTOR_EMAIL)
        if settings.EMAIL_QUEUE_ENABLED:
            await email_queue_service.enqueue_two_factor_code_email(email, code, first_name)
        else:
            await email_service.send_two_factor_code_email(email, code, first_name)
        return code

    async def cleanup_expired_codes(self) -> int:
        """Delete expired verification codes."""
        stmt = select(VerificationCode).where(
            VerificationCode.expires_at < datetime.now(timezone.utc)
        )
        result = await self.session.execute(stmt)
        expired_codes = result.scalars().all()

        count = len(expired_codes)
        for code in expired_codes:
            await self.session.delete(code)

        await self.session.flush()

        if count > 0:
            logger.info("verification_code.cleanup", expired_count=count)

        return count
