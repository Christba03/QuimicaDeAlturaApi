from datetime import datetime
from uuid import UUID
from typing import Any, Optional

from pydantic import BaseModel


class ExternalApiBase(BaseModel):
    name: str
    base_url: str
    description: Optional[str] = None
    auth_type: Optional[str] = None
    rate_limit: Optional[int] = None
    is_active: bool = True
    endpoints: Optional[list[Any]] = None


class ExternalApiCreate(ExternalApiBase):
    pass


class ExternalApiUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    description: Optional[str] = None
    auth_type: Optional[str] = None
    rate_limit: Optional[int] = None
    is_active: Optional[bool] = None
    endpoints: Optional[list[Any]] = None


class ExternalApiResponse(ExternalApiBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExternalApiListResponse(BaseModel):
    items: list[ExternalApiResponse]
    total: int
    page: int
    size: int
    pages: int
