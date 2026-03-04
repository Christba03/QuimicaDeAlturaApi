import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    scopes: list[str] = Field(default_factory=list, description="Permission scopes for this key")
    expires_at: datetime | None = None


class APIKeyCreatedResponse(BaseModel):
    """Returned once at creation — includes the plaintext key (never stored)."""
    id: uuid.UUID
    name: str
    key: str                # plaintext key — shown only once
    key_prefix: str
    scopes: list[str]
    expires_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class APIKeyResponse(BaseModel):
    """Safe representation — no plaintext key."""
    id: uuid.UUID
    name: str
    key_prefix: str
    scopes: list[str]
    is_active: bool
    expires_at: datetime | None
    last_used_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class APIKeyValidateRequest(BaseModel):
    key: str


class APIKeyValidateResponse(BaseModel):
    valid: bool
    user_id: uuid.UUID | None = None
    scopes: list[str] = []
