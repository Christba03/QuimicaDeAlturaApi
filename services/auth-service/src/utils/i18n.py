"""
Minimal i18n support for email notifications.
Uses a simple dictionary-based translation approach (no heavy dependencies).
Supports: en (English), es (Spanish).
"""
from __future__ import annotations

# Default (fallback) locale
DEFAULT_LOCALE = "en"

# Supported locales
SUPPORTED_LOCALES = {"en", "es"}

_TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        # Verification
        "verify_email_subject": "Verify Your Email Address",
        "verify_email_heading": "Verify Your Email",
        "verify_email_greeting": "Hello {name},",
        "verify_email_body": "Thank you for registering! Please verify your email address by entering this code:",
        "verify_email_expiry": "This code will expire in {minutes} minutes.",
        "verify_email_ignore": "If you didn't create an account, please ignore this email.",
        # Password reset
        "password_reset_subject": "Reset Your Password",
        "password_reset_heading": "Reset Your Password",
        "password_reset_greeting": "Hello {name},",
        "password_reset_body": "You requested to reset your password. Please use this code:",
        "password_reset_expiry": "This code will expire in {minutes} minutes.",
        "password_reset_ignore": "If you didn't request a password reset, please ignore this email.",
        # 2FA code
        "two_factor_subject": "Your Two-Factor Authentication Code",
        "two_factor_heading": "Two-Factor Authentication Code",
        "two_factor_greeting": "Hello {name},",
        "two_factor_body": "Your two-factor authentication code is:",
        "two_factor_expiry": "This code will expire in 10 minutes.",
        "two_factor_warning": "If you didn't request this code, please secure your account immediately.",
        # Security notification
        "security_notification_subject": "Security Alert: {event_type}",
        "security_notification_heading": "Security Alert: {event_type}",
        "security_notification_greeting": "Hello {name},",
        "security_notification_footer": "If this wasn't you, please secure your account immediately.",
    },
    "es": {
        # Verification
        "verify_email_subject": "Verifica tu correo electrónico",
        "verify_email_heading": "Verifica tu correo electrónico",
        "verify_email_greeting": "Hola {name},",
        "verify_email_body": "¡Gracias por registrarte! Por favor verifica tu correo electrónico ingresando este código:",
        "verify_email_expiry": "Este código expirará en {minutes} minutos.",
        "verify_email_ignore": "Si no creaste una cuenta, por favor ignora este correo.",
        # Password reset
        "password_reset_subject": "Restablece tu contraseña",
        "password_reset_heading": "Restablece tu contraseña",
        "password_reset_greeting": "Hola {name},",
        "password_reset_body": "Solicitaste restablecer tu contraseña. Por favor usa este código:",
        "password_reset_expiry": "Este código expirará en {minutes} minutos.",
        "password_reset_ignore": "Si no solicitaste un restablecimiento de contraseña, por favor ignora este correo.",
        # 2FA code
        "two_factor_subject": "Tu código de autenticación de dos factores",
        "two_factor_heading": "Código de autenticación de dos factores",
        "two_factor_greeting": "Hola {name},",
        "two_factor_body": "Tu código de autenticación de dos factores es:",
        "two_factor_expiry": "Este código expirará en 10 minutos.",
        "two_factor_warning": "Si no solicitaste este código, asegura tu cuenta de inmediato.",
        # Security notification
        "security_notification_subject": "Alerta de seguridad: {event_type}",
        "security_notification_heading": "Alerta de seguridad: {event_type}",
        "security_notification_greeting": "Hola {name},",
        "security_notification_footer": "Si no fuiste tú, asegura tu cuenta de inmediato.",
    },
}


def detect_locale(accept_language: str | None) -> str:
    """
    Detect the preferred locale from an Accept-Language header value.
    Returns the best matching supported locale, defaulting to 'en'.

    Example: "es-MX,es;q=0.9,en-US;q=0.8" → "es"
    """
    if not accept_language:
        return DEFAULT_LOCALE

    for segment in accept_language.replace(" ", "").split(","):
        lang = segment.split(";")[0].strip().lower()
        # Try exact match first, then language prefix
        if lang in SUPPORTED_LOCALES:
            return lang
        prefix = lang.split("-")[0]
        if prefix in SUPPORTED_LOCALES:
            return prefix

    return DEFAULT_LOCALE


def t(key: str, locale: str = DEFAULT_LOCALE, **kwargs) -> str:
    """
    Translate a key to the given locale, with optional string formatting.
    Falls back to English if the key is not found in the requested locale.
    """
    locale = locale if locale in SUPPORTED_LOCALES else DEFAULT_LOCALE
    translations = _TRANSLATIONS.get(locale, _TRANSLATIONS[DEFAULT_LOCALE])
    template = translations.get(key) or _TRANSLATIONS[DEFAULT_LOCALE].get(key, key)
    if kwargs:
        try:
            return template.format(**kwargs)
        except KeyError:
            return template
    return template
