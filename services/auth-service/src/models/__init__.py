from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from src.models.user import User  # noqa: E402, F401
from src.models.role import Role, Permission, role_permissions, user_roles  # noqa: E402, F401
from src.models.session import UserSession  # noqa: E402, F401
from src.models.verification_code import VerificationCode, VerificationCodeType  # noqa: E402, F401
from src.models.two_factor import TwoFactorBackupCode  # noqa: E402, F401
from src.models.security_event import SecurityEvent, SecurityEventType  # noqa: E402, F401
from src.models.oauth_account import OAuthAccount  # noqa: E402, F401
from src.models.api_key import APIKey  # noqa: E402, F401
from src.models.policy import Policy  # noqa: E402, F401
from src.models.settings import AppSettings  # noqa: E402, F401