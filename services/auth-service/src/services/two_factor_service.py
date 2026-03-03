import base64
import secrets
import uuid
from datetime import datetime, timezone
from io import BytesIO

import pyotp
import qrcode
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models.two_factor import TwoFactorBackupCode
from src.models.user import User
from src.utils.security import hash_password, verify_password

logger = structlog.get_logger()


class TwoFactorService:
    """Service for handling two-factor authentication."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def generate_totp_secret(self) -> str:
        """Generate a new TOTP secret."""
        return pyotp.random_base32()

    def get_totp_uri(self, email: str, secret: str) -> str:
        """Generate TOTP URI for QR code."""
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(
            name=email,
            issuer_name=settings.TWO_FACTOR_ISSUER_NAME,
        )

    def generate_qr_code(self, uri: str) -> str:
        """Generate QR code as base64 string."""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_base64}"

    def verify_totp(self, secret: str, code: str) -> bool:
        """Verify a TOTP code."""
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)  # Allow 1 time step tolerance

    def generate_backup_codes(self, count: int = 10) -> list[str]:
        """Generate backup codes."""
        codes = []
        for _ in range(count):
            # Generate 8-digit code
            code = f"{secrets.randbelow(90000000) + 10000000:08d}"
            codes.append(code)
        return codes

    async def create_backup_codes(self, user_id: uuid.UUID, codes: list[str]) -> list[TwoFactorBackupCode]:
        """Create backup codes in database."""
        backup_code_objects = []
        for code in codes:
            code_hash = hash_password(code)
            backup_code = TwoFactorBackupCode(
                user_id=user_id,
                code_hash=code_hash,
            )
            backup_code_objects.append(backup_code)
            self.session.add(backup_code)

        await self.session.flush()
        logger.info("two_factor.backup_codes_created", user_id=str(user_id), count=len(codes))
        return backup_code_objects

    async def verify_backup_code(self, user_id: uuid.UUID, code: str) -> bool:
        """Verify a backup code and mark it as used."""
        stmt = select(TwoFactorBackupCode).where(
            TwoFactorBackupCode.user_id == user_id,
            TwoFactorBackupCode.used_at.is_(None),
        )

        result = await self.session.execute(stmt)
        backup_codes = result.scalars().all()

        for backup_code in backup_codes:
            if verify_password(code, backup_code.code_hash):
                backup_code.used_at = datetime.now(timezone.utc)
                await self.session.flush()

                logger.info("two_factor.backup_code_used", user_id=str(user_id), code_id=str(backup_code.id))
                return True

        logger.warning("two_factor.backup_code_invalid", user_id=str(user_id))
        return False

    async def get_unused_backup_codes_count(self, user_id: uuid.UUID) -> int:
        """Get count of unused backup codes."""
        stmt = select(TwoFactorBackupCode).where(
            TwoFactorBackupCode.user_id == user_id,
            TwoFactorBackupCode.used_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return len(result.scalars().all())

    async def delete_all_backup_codes(self, user_id: uuid.UUID) -> int:
        """Delete all backup codes for a user."""
        stmt = select(TwoFactorBackupCode).where(TwoFactorBackupCode.user_id == user_id)
        result = await self.session.execute(stmt)
        codes = result.scalars().all()

        count = len(codes)
        for code in codes:
            await self.session.delete(code)

        await self.session.flush()
        logger.info("two_factor.backup_codes_deleted", user_id=str(user_id), count=count)
        return count
