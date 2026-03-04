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
from src.services.webhook_service import webhook_service

logger = structlog.get_logger()

# Redis key prefixes for IP-level lockout
_IP_FAIL_PREFIX = "ip:failed_logins:"
_IP_LOCK_PREFIX = "ip:lockout:"


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

        # Lock expired — unlock
        user.locked_until = None
        user.failed_login_attempts = 0
        await self.session.flush()
        return False

    async def handle_failed_login(self, user: User, ip_address: str | None = None) -> bool:
        """Handle a failed login attempt. Returns True if account should be locked."""
        user.failed_login_attempts += 1

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

            await webhook_service.emit(
                "ACCOUNT_LOCKED",
                user_id=str(user.id),
                data={"ip_address": ip_address, "failed_attempts": user.failed_login_attempts},
            )
            await self.session.flush()
            return True

        await self.session.flush()
        return False

    async def handle_successful_login(self, user: User, ip_address: str | None = None) -> None:
        """Handle a successful login."""
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

    # -----------------------------------------------------------------------
    # IP-level brute force protection (Redis-backed)
    # -----------------------------------------------------------------------

    async def record_ip_failed_login(self, ip_address: str, redis_client) -> bool:
        """
        Increment the failed-login counter for an IP.
        Returns True if the IP has been locked out after this attempt.
        """
        if not ip_address:
            return False

        fail_key = f"{_IP_FAIL_PREFIX}{ip_address}"
        lock_key = f"{_IP_LOCK_PREFIX}{ip_address}"
        window = settings.IP_LOCKOUT_WINDOW_MINUTES * 60

        try:
            count = await redis_client.incr(fail_key)
            if count == 1:
                await redis_client.expire(fail_key, window)

            if count >= settings.IP_LOCKOUT_THRESHOLD:
                lockout_ttl = settings.IP_LOCKOUT_DURATION_MINUTES * 60
                await redis_client.setex(lock_key, lockout_ttl, "1")
                logger.warning(
                    "security.ip_locked_out",
                    ip_address=ip_address,
                    failed_count=count,
                )
                return True
        except Exception as e:
            logger.error("security.ip_fail_record_error", ip_address=ip_address, error=str(e))

        return False

    async def is_ip_locked(self, ip_address: str, redis_client) -> bool:
        """Return True if the IP is currently locked out."""
        if not ip_address:
            return False
        try:
            result = await redis_client.get(f"{_IP_LOCK_PREFIX}{ip_address}")
            return result is not None
        except Exception as e:
            logger.error("security.ip_lock_check_error", ip_address=ip_address, error=str(e))
            return False

    async def clear_ip_lockout(self, ip_address: str, redis_client) -> None:
        """Clear IP lockout (admin action)."""
        try:
            await redis_client.delete(f"{_IP_LOCK_PREFIX}{ip_address}")
            await redis_client.delete(f"{_IP_FAIL_PREFIX}{ip_address}")
        except Exception as e:
            logger.error("security.ip_lock_clear_error", ip_address=ip_address, error=str(e))

    # -----------------------------------------------------------------------
    # GeoIP resolution
    # -----------------------------------------------------------------------

    async def resolve_geoip(self, ip_address: str | None) -> dict:
        """
        Look up geographic information for an IP address using ip-api.com (free tier).
        Returns an empty dict on failure or when GeoIP is disabled.
        """
        if not settings.GEOIP_ENABLED or not ip_address:
            return {}

        # Skip private / loopback addresses
        _private_prefixes = ("10.", "172.", "192.168.", "127.", "::1", "localhost")
        if any(ip_address.startswith(p) for p in _private_prefixes):
            return {}

        try:
            import httpx  # soft dependency — already in oauth requirements
            url = settings.GEOIP_API_URL.format(ip=ip_address)
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("status") == "success":
                        return {
                            "country_code": data.get("countryCode"),
                            "country_name": data.get("country"),
                            "region_name": data.get("regionName"),
                            "city": data.get("city"),
                            "latitude": data.get("lat"),
                            "longitude": data.get("lon"),
                        }
        except Exception as e:
            logger.debug("geoip.lookup_failed", ip=ip_address, error=str(e))

        return {}

    # -----------------------------------------------------------------------
    # Suspicious activity detection
    # -----------------------------------------------------------------------

    async def detect_suspicious_activity(
        self, user: User, ip_address: str | None = None, user_agent: str | None = None
    ) -> bool:
        """Detect suspicious activity (new device, new location, etc.)."""
        if user.last_login_ip and ip_address and user.last_login_ip != ip_address:
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
