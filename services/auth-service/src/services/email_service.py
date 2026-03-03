import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import structlog
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path

from src.config import settings

logger = structlog.get_logger()

# Setup Jinja2 environment for email templates
template_dir = Path(__file__).parent.parent / "templates" / "email"
template_dir.mkdir(parents=True, exist_ok=True)
env = Environment(
    loader=FileSystemLoader(str(template_dir)),
    autoescape=select_autoescape(["html", "xml"]),
)


class EmailService:
    """Service for sending emails via SMTP."""

    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_from = settings.SMTP_FROM
        self.smtp_from_name = settings.SMTP_FROM_NAME
        self.use_tls = settings.SMTP_USE_TLS

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """Send an email."""
        try:
            message = MIMEMultipart("alternative")
            message["From"] = f"{self.smtp_from_name} <{self.smtp_from}>"
            message["To"] = to_email
            message["Subject"] = subject

            # Add text and HTML parts
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)

            html_part = MIMEText(html_content, "html")
            message.attach(html_part)

            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user if self.smtp_user else None,
                password=self.smtp_password if self.smtp_password else None,
                use_tls=self.use_tls,
            )

            logger.info("email.sent", to=to_email, subject=subject)
            return True
        except Exception as e:
            logger.error("email.send_failed", to=to_email, error=str(e))
            return False

    async def send_verification_email(self, to_email: str, code: str, first_name: Optional[str] = None) -> bool:
        """Send email verification code."""
        try:
            # Try to load template, fallback to simple HTML if template not found
            try:
        template = env.get_template("verification.html")
        html_content = template.render(code=code, first_name=first_name or "User")
            except Exception:
                html_content = f"""
                <html><body>
                    <h1>Verify Your Email</h1>
                    <p>Hello {first_name or 'User'},</p>
                    <p>Your verification code is: <strong>{code}</strong></p>
                    <p>This code expires in {settings.EMAIL_VERIFICATION_CODE_EXPIRY_MINUTES} minutes.</p>
                </body></html>
                """

            text_content = f"""
Hello {first_name or 'User'},

Thank you for registering! Please verify your email address by entering this code:

{code}

This code will expire in {settings.EMAIL_VERIFICATION_CODE_EXPIRY_MINUTES} minutes.

If you didn't create an account, please ignore this email.
"""

        return await self.send_email(
            to_email=to_email,
                subject="Verify Your Email Address",
            html_content=html_content,
            text_content=text_content,
        )
        except Exception as e:
            logger.error("email.verification_failed", to=to_email, error=str(e))
            return False

    async def send_password_reset_email(self, to_email: str, code: str, first_name: Optional[str] = None) -> bool:
        """Send password reset code."""
        try:
            try:
        template = env.get_template("password_reset.html")
        html_content = template.render(code=code, first_name=first_name or "User")
            except Exception:
                html_content = f"""
                <html><body>
                    <h1>Reset Your Password</h1>
                    <p>Hello {first_name or 'User'},</p>
                    <p>Your password reset code is: <strong>{code}</strong></p>
                    <p>This code expires in {settings.PASSWORD_RESET_CODE_EXPIRY_MINUTES} minutes.</p>
                </body></html>
                """

            text_content = f"""
Hello {first_name or 'User'},

You requested to reset your password. Please use this code:

{code}

This code will expire in {settings.PASSWORD_RESET_CODE_EXPIRY_MINUTES} minutes.

If you didn't request a password reset, please ignore this email.
"""

        return await self.send_email(
            to_email=to_email,
                subject="Reset Your Password",
            html_content=html_content,
            text_content=text_content,
        )
        except Exception as e:
            logger.error("email.password_reset_failed", to=to_email, error=str(e))
            return False

    async def send_two_factor_code_email(self, to_email: str, code: str, first_name: Optional[str] = None) -> bool:
        """Send 2FA code via email."""
        try:
            try:
                template = env.get_template("two_factor_code.html")
        html_content = template.render(code=code, first_name=first_name or "User")
            except Exception:
                html_content = f"""
                <html><body>
                    <h1>Two-Factor Authentication Code</h1>
                    <p>Hello {first_name or 'User'},</p>
                    <p>Your 2FA code is: <strong>{code}</strong></p>
                    <p>This code expires in 10 minutes.</p>
                </body></html>
                """

            text_content = f"""
Hello {first_name or 'User'},

Your two-factor authentication code is:

{code}

This code will expire in 10 minutes.

If you didn't request this code, please secure your account immediately.
"""

        return await self.send_email(
            to_email=to_email,
                subject="Your Two-Factor Authentication Code",
            html_content=html_content,
            text_content=text_content,
        )
        except Exception as e:
            logger.error("email.two_factor_failed", to=to_email, error=str(e))
            return False

    async def send_security_notification(
        self,
        to_email: str,
        event_type: str,
        message: str,
        first_name: Optional[str] = None,
    ) -> bool:
        """Send security event notification."""
        try:
            try:
        template = env.get_template("security_notification.html")
        html_content = template.render(
            event_type=event_type,
                    message=message,
            first_name=first_name or "User",
        )
            except Exception:
                html_content = f"""
                <html><body>
                    <h1>Security Alert: {event_type}</h1>
                    <p>Hello {first_name or 'User'},</p>
                    <p>{message}</p>
                </body></html>
                """

            text_content = f"""
Hello {first_name or 'User'},

Security Alert: {event_type}

{message}

If this wasn't you, please secure your account immediately.
"""

        return await self.send_email(
            to_email=to_email,
            subject=f"Security Alert: {event_type}",
            html_content=html_content,
            text_content=text_content,
        )
        except Exception as e:
            logger.error("email.security_notification_failed", to=to_email, error=str(e))
            return False


# Singleton instance
email_service = EmailService()
