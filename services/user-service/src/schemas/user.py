import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserPreferences(BaseModel):
    language: str = Field(default="es", description="Preferred language code")
    measurement_unit: str = Field(default="metric", description="metric or imperial")
    altitude_unit: str = Field(default="meters", description="meters or feet")
    notifications_enabled: bool = Field(default=True)
    newsletter_subscribed: bool = Field(default=False)
    default_region: Optional[str] = Field(default=None, description="Preferred geographic region")
    theme: str = Field(default="light", description="UI theme preference")


class UserProfileBase(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    altitude_meters: Optional[float] = Field(default=None, description="User's altitude in meters")
    expertise_level: str = Field(
        default="beginner",
        description="beginner, intermediate, advanced, expert",
    )
    birthdate: Optional[str] = Field(default=None, description="ISO date string YYYY-MM-DD")
    nationality: Optional[str] = None
    address: Optional[str] = None


class UserProfileUpdate(UserProfileBase):
    preferences: Optional[UserPreferences] = None


class UserProfileResponse(UserProfileBase):
    id: uuid.UUID
    email: Optional[str] = None
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    favorites_count: int = 0
    reports_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserProfileCreate(UserProfileBase):
    id: uuid.UUID
    email: str
    preferences: UserPreferences = Field(default_factory=UserPreferences)
