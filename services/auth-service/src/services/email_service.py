import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

import structlog
from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.config import settings
from src.utils.i18n import detect_locale, t

logger = structlog.get_logger()

# Jinja2 environment for email templates
template_dir = Path(__file__).parent.parent / "templates" / "email"
template_dir.mkdir(parents=True, exist_ok=True)
env = Environment(
    loader=FileSystemLoader(str(template_dir)),
    autoescape=select_autoescape(["html", "xml"]),
)


class EmailService:
    """Service for sending emails via SMTP with i18n support."""

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
            message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM}>"
            message["To"] = to_email
            message["Subject"] = subject

            if text_content:
                message.attach(MIMEText(text_content, "plain"))
            message.attach(MIMEText(html_content, "html"))

            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER if settings.SMTP_USER else None,
                password=settings.SMTP_PASSWORD if settings.SMTP_PASSWORD else None,
                use_tls=settings.SMTP_USE_TLS,
            )

            logger.info("email.sent", to=to_email, subject=subject)
            return True
        except Exception as e:
            logger.error("email.send_failed", to=to_email, error=str(e))
            return False

    async def send_verification_email(
        self,
        to_email: str,
        code: str,
        first_name: Optional[str] = None,
        accept_language: Optional[str] = None,
    ) -> bool:
        """Send email verification code."""
        locale = detect_locale(accept_language)
        name = first_name or "User"
        try:
            i18n_ctx = {
                "heading": t("verify_email_heading", locale),
                "greeting": t("verify_email_greeting", locale, name=name),
                "body": t("verify_email_body", locale),
                "expiry": t("verify_email_expiry", locale, minutes=settings.EMAIL_VERIFICATION_CODE_EXPIRY_MINUTES),
                "ignore": t("verify_email_ignore", locale),
                "code": code,
                "first_name": name,
            }
            try:
                template = env.get_template("verification.html")
                html_content = template.render(**i18n_ctx)
            except Exception:
                html_content = (
                    f"<html><body>"
                    f"<h1>{i18n_ctx['heading']}</h1>"
                    f"<p>{i18n_ctx['greeting']}</p>"
                    f"<p>{i18n_ctx['body']} <strong>{code}</strong></p>"
                    f"<p>{i18n_ctx['expiry']}</p>"
                    f"<p>{i18n_ctx['ignore']}</p>"
                    f"</body></html>"
                )

            text_content = (
                f"{i18n_ctx['greeting']}\n\n"
                f"{i18n_ctx['body']}\n\n{code}\n\n"
                f"{i18n_ctx['expiry']}\n{i18n_ctx['ignore']}"
            )

            return await self.send_email(
                to_email=to_email,
                subject=t("verify_email_subject", locale),
                html_content=html_content,
                text_content=text_content,
            )
        except Exception as e:
            logger.error("email.verification_failed", to=to_email, error=str(e))
            return False

    async def send_password_reset_email(
        self,
        to_email: str,
        code: str,
        first_name: Optional[str] = None,
        accept_language: Optional[str] = None,
    ) -> bool:
        """Send password reset code."""
        locale = detect_locale(accept_language)
        name = first_name or "User"
        try:
            i18n_ctx = {
                "heading": t("password_reset_heading", locale),
                "greeting": t("password_reset_greeting", locale, name=name),
                "body": t("password_reset_body", locale),
                "expiry": t("password_reset_expiry", locale, minutes=settings.PASSWORD_RESET_CODE_EXPIRY_MINUTES),
                "ignore": t("password_reset_ignore", locale),
                "code": code,
                "first_name": name,
            }
            try:
                template = env.get_template("password_reset.html")
                html_content = template.render(**i18n_ctx)
            except Exception:
                html_content = (
                    f"<html><body>"
                    f"<h1>{i18n_ctx['heading']}</h1>"
                    f"<p>{i18n_ctx['greeting']}</p>"
                    f"<p>{i18n_ctx['body']} <strong>{code}</strong></p>"
                    f"<p>{i18n_ctx['expiry']}</p>"
                    f"<p>{i18n_ctx['ignore']}</p>"
                    f"</body></html>"
                )

            text_content = (
                f"{i18n_ctx['greeting']}\n\n"
                f"{i18n_ctx['body']}\n\n{code}\n\n"
                f"{i18n_ctx['expiry']}\n{i18n_ctx['ignore']}"
            )

            return await self.send_email(
                to_email=to_email,
                subject=t("password_reset_subject", locale),
                html_content=html_content,
                text_content=text_content,
            )
        except Exception as e:
            logger.error("email.password_reset_failed", to=to_email, error=str(e))
            return False

    async def send_two_factor_code_email(
        self,
        to_email: str,
        code: str,
        first_name: Optional[str] = None,
        accept_language: Optional[str] = None,
    ) -> bool:
        """Send 2FA code via email."""
        locale = detect_locale(accept_language)
        name = first_name or "User"
        try:
            i18n_ctx = {
                "heading": t("two_factor_heading", locale),
                "greeting": t("two_factor_greeting", locale, name=name),
                "body": t("two_factor_body", locale),
                "expiry": t("two_factor_expiry", locale),
                "warning": t("two_factor_warning", locale),
                "code": code,
                "first_name": name,
            }
            try:
                template = env.get_template("two_factor_code.html")
                html_content = template.render(**i18n_ctx)
            except Exception:
                html_content = (
                    f"<html><body>"
                    f"<h1>{i18n_ctx['heading']}</h1>"
                    f"<p>{i18n_ctx['greeting']}</p>"
                    f"<p>{i18n_ctx['body']} <strong>{code}</strong></p>"
                    f"<p>{i18n_ctx['expiry']}</p>"
                    f"<p>{i18n_ctx['warning']}</p>"
                    f"</body></html>"
                )

            text_content = (
                f"{i18n_ctx['greeting']}\n\n"
                f"{i18n_ctx['body']}\n\n{code}\n\n"
                f"{i18n_ctx['expiry']}\n{i18n_ctx['warning']}"
            )

            return await self.send_email(
                to_email=to_email,
                subject=t("two_factor_subject", locale),
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
        accept_language: Optional[str] = None,
    ) -> bool:
        """Send security event notification."""
        locale = detect_locale(accept_language)
        name = first_name or "User"
        try:
            i18n_ctx = {
                "heading": t("security_notification_heading", locale, event_type=event_type),
                "greeting": t("security_notification_greeting", locale, name=name),
                "message": message,
                "footer": t("security_notification_footer", locale),
                "event_type": event_type,
                "first_name": name,
            }
            try:
                template = env.get_template("security_notification.html")
                html_content = template.render(**i18n_ctx)
            except Exception:
                html_content = (
                    f"<html><body>"
                    f"<h1>{i18n_ctx['heading']}</h1>"
                    f"<p>{i18n_ctx['greeting']}</p>"
                    f"<p>{message}</p>"
                    f"<p>{i18n_ctx['footer']}</p>"
                    f"</body></html>"
                )

            text_content = (
                f"{i18n_ctx['greeting']}\n\n"
                f"{i18n_ctx['heading']}\n\n{message}\n\n"
                f"{i18n_ctx['footer']}"
            )

            return await self.send_email(
                to_email=to_email,
                subject=t("security_notification_subject", locale, event_type=event_type),
                html_content=html_content,
                text_content=text_content,
            )
        except Exception as e:
            logger.error("email.security_notification_failed", to=to_email, error=str(e))
            return False


# Singleton instance
email_service = EmailService()
