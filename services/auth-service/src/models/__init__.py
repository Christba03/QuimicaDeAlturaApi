from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from src.models.user import User  # noqa: E402, F401
from src.models.role import Role, Permission, role_permissions, user_roles  # noqa: E402, F401
from src.models.session import UserSession  # noqa: E402, F401
