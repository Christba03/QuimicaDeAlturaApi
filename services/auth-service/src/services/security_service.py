import uuid
from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models.security_event import SecurityEvent, SecurityEventType
from src.models.user import User
from src.repositories.user_repository import UserRepository
from src.services.email_queue import email_queue_service
from src.services.email_service import email_service

logger = structlog.get_logger()


class SecurityService:
    """Service for security-related operations: rate limiting, account lockout, audit logging."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def log_security_event(
        self,
        event_type: SecurityEventType,
        user_id: uuid.UUID | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata: dict | None = None,
    ) -> SecurityEvent:
        """Log a security event."""
        event = SecurityEvent(
            user_id=user_id,
            event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {},
        )
        self.session.add(event)
        await self.session.flush()

        logger.info(
            "security_event.logged",
            event_type=event_type.value,
            user_id=str(user_id) if user_id else None,
        )

        return event

    async def check_account_locked(self, user: User) -> bool:
        """Check if account is locked."""
        if user.locked_until is None:
            return False

        if user.locked_until > datetime.now(timezone.utc):
            return True

        # Lock expired, unlock account
        user.locked_until = None
        user.failed_login_attempts = 0
        await self.session.flush()
        return False

    async def handle_failed_login(self, user: User, ip_address: str | None = None) -> bool:
        """Handle a failed login attempt. Returns True if account should be locked."""
        user.failed_login_attempts += 1

        # Log the failed attempt
        await self.log_security_event(
            SecurityEventType.LOGIN_FAILED,
            user_id=user.id,
            ip_address=ip_address,
            metadata={"attempt_number": user.failed_login_attempts},
        )

        # Lock account if max attempts reached
        if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
            lockout_duration = timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)
            user.locked_until = datetime.now(timezone.utc) + lockout_duration

            await self.log_security_event(
                SecurityEventType.ACCOUNT_LOCKED,
                user_id=user.id,
                ip_address=ip_address,
                metadata={
                    "failed_attempts": user.failed_login_attempts,
                    "locked_until": user.locked_until.isoformat(),
                },
            )

            # Send security notification email
            message = (
                f"Your account has been locked due to {user.failed_login_attempts} failed login attempts. "
                f"It will be unlocked automatically after {settings.LOCKOUT_DURATION_MINUTES} minutes."
            )
            if settings.EMAIL_QUEUE_ENABLED:
                await email_queue_service.enqueue_security_notification(
                    user.email, "Account Locked", message, user.first_name
                )
            else:
                await email_service.send_security_notification(
                    user.email, "Account Locked", message, user.first_name
                )

            await self.session.flush()
            return True

        await self.session.flush()
        return False

    async def handle_successful_login(self, user: User, ip_address: str | None = None) -> None:
        """Handle a successful login."""
        # Reset failed attempts
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.now(timezone.utc)
        user.last_login_ip = ip_address

        await self.log_security_event(
            SecurityEventType.LOGIN_SUCCESS,
            user_id=user.id,
            ip_address=ip_address,
        )

        await self.session.flush()

    async def check_rate_limit(self, identifier: str, limit: int, window_minutes: int = 15) -> bool:
        """Check rate limit for an identifier (email or IP). Returns True if within limit."""
        # This is a simplified version - in production, use Redis for distributed rate limiting
        # For now, we'll use a simple in-memory approach or database-based tracking
        # TODO: Implement Redis-based rate limiting for production
        return True  # Placeholder - implement proper rate limiting

    async def detect_suspicious_activity(
        self, user: User, ip_address: str | None = None, user_agent: str | None = None
    ) -> bool:
        """Detect suspicious activity (new device, new location, etc.)."""
        # Check if IP changed significantly
        if user.last_login_ip and ip_address and user.last_login_ip != ip_address:
            # Log suspicious activity
            await self.log_security_event(
                SecurityEventType.SUSPICIOUS_ACTIVITY,
                user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={
                    "previous_ip": user.last_login_ip,
                    "current_ip": ip_address,
                    "reason": "ip_change",
                },
            )

            # Send notification
            message = (
                f"A login was detected from a new IP address: {ip_address}. "
                "If this wasn't you, please secure your account immediately."
            )
            if settings.EMAIL_QUEUE_ENABLED:
                await email_queue_service.enqueue_security_notification(
                    user.email, "Suspicious Login Detected", message, user.first_name
                )
            else:
                await email_service.send_security_notification(
                    user.email, "Suspicious Login Detected", message, user.first_name
                )

            return True

        return False
