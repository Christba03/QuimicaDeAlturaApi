from datetime import datetime, timezone
from enum import Enum
from typing import Optional

import structlog
from arq import ArqRedis, create_pool
from arq.connections import RedisSettings

from src.config import settings

logger = structlog.get_logger()


class EmailPriority(str, Enum):
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class EmailQueueService:
    """Service for queuing emails asynchronously."""

    def __init__(self):
        self.redis_pool: Optional[ArqRedis] = None
        self._initialized = False

    async def initialize(self):
        """Initialize Redis connection pool for ARQ."""
        if self._initialized:
            return

        redis_settings = RedisSettings.from_dsn(settings.redis_url)
        self.redis_pool = await create_pool(redis_settings)
        self._initialized = True
        logger.info("email_queue.initialized")

    async def close(self):
        """Close Redis connection pool."""
        if self.redis_pool:
            await self.redis_pool.close()
            self._initialized = False
            logger.info("email_queue.closed")

    async def enqueue_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        priority: EmailPriority = EmailPriority.NORMAL,
    ) -> bool:
        """Enqueue an email to be sent asynchronously."""
        if not settings.EMAIL_QUEUE_ENABLED:
            # Fallback to synchronous sending if queue is disabled
            from src.services.email_service import email_service
            return await email_service.send_email(to_email, subject, html_content, text_content)

        if not self._initialized:
            await self.initialize()

        try:
            job = await self.redis_pool.enqueue_job(
                "send_email_task",
                to_email,
                subject,
                html_content,
                text_content,
                _job_id=f"email:{to_email}:{datetime.now(timezone.utc).isoformat()}",
            )
            logger.info("email.enqueued", to=to_email, subject=subject, job_id=job.job_id)
            return True
        except Exception as e:
            logger.error("email.enqueue_failed", to=to_email, error=str(e))
            # Fallback to synchronous sending on error
            from src.services.email_service import email_service
            return await email_service.send_email(to_email, subject, html_content, text_content)

    async def enqueue_verification_email(
        self, to_email: str, code: str, first_name: Optional[str] = None
    ) -> bool:
        """Enqueue email verification code email."""
        return await self.enqueue_email(
            to_email=to_email,
            subject="Verify Your Email Address",
            html_content=f"<h1>Your verification code: {code}</h1>",
            text_content=f"Your verification code: {code}",
            priority=EmailPriority.HIGH,
        )

    async def enqueue_password_reset_email(
        self, to_email: str, code: str, first_name: Optional[str] = None
    ) -> bool:
        """Enqueue password reset email."""
        from jinja2 import Environment, FileSystemLoader
        from pathlib import Path
        
        template_dir = Path(__file__).parent.parent / "templates" / "email"
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        
        try:
            template = env.get_template("password_reset.html")
            html_content = template.render(code=code, first_name=first_name or "User")
        except Exception:
            html_content = f"<h1>Your password reset code: {code}</h1>"
        
        text_content = f"Your password reset code: {code}"
        
        return await self.enqueue_email(
            to_email=to_email,
            subject="Reset Your Password",
            html_content=html_content,
            text_content=text_content,
            priority=EmailPriority.HIGH,
        )

    async def enqueue_two_factor_code_email(
        self, to_email: str, code: str, first_name: Optional[str] = None
    ) -> bool:
        """Enqueue 2FA code email."""
        from jinja2 import Environment, FileSystemLoader
        from pathlib import Path
        
        template_dir = Path(__file__).parent.parent / "templates" / "email"
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        
        try:
            template = env.get_template("two_factor_code.html")
            html_content = template.render(code=code, first_name=first_name or "User")
        except Exception:
            html_content = f"<h1>Your 2FA code: {code}</h1>"
        
        text_content = f"Your 2FA code: {code}"
        
        return await self.enqueue_email(
            to_email=to_email,
            subject="Your Two-Factor Authentication Code",
            html_content=html_content,
            text_content=text_content,
            priority=EmailPriority.HIGH,
        )

    async def enqueue_security_notification(
        self,
        to_email: str,
        event_type: str,
        message: str,
        first_name: Optional[str] = None,
    ) -> bool:
        """Enqueue security notification email."""
        from jinja2 import Environment, FileSystemLoader
        from pathlib import Path
        
        template_dir = Path(__file__).parent.parent / "templates" / "email"
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        
        try:
            template = env.get_template("security_notification.html")
            html_content = template.render(
                event_type=event_type,
                message=message,
                first_name=first_name or "User",
            )
        except Exception:
            html_content = f"<h1>Security Alert</h1><p>{message}</p>"
        
        return await self.enqueue_email(
            to_email=to_email,
            subject=f"Security Alert: {event_type}",
            html_content=html_content,
            text_content=message,
            priority=EmailPriority.NORMAL,
        )


# Singleton instance
email_queue_service = EmailQueueService()
