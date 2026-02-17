from enum import Enum

from pydantic import BaseModel


class UserEventType(str, Enum):
    USER_REGISTERED = "user.registered"
    USER_LOGIN = "user.login"
    USER_SEARCH = "user.search"
    USER_FAVORITE_ADDED = "user.favorite.added"
    USER_FAVORITE_REMOVED = "user.favorite.removed"


class UserEvent(BaseModel):
    event_type: UserEventType
    user_id: str
    data: dict | None = None
