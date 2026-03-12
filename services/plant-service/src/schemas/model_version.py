from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel

from src.models.model_version import ModelStatus


class ModelVersionBase(BaseModel):
    name: str
    version: str
    accuracy: Optional[float] = None
    type: Optional[str] = None
    status: Optional[ModelStatus] = ModelStatus.testing
    deployed_at: Optional[datetime] = None
    notes: Optional[str] = None
    can_rollback: bool = True


class ModelVersionCreate(ModelVersionBase):
    pass


class ModelVersionUpdate(BaseModel):
    name: Optional[str] = None
    version: Optional[str] = None
    accuracy: Optional[float] = None
    type: Optional[str] = None
    status: Optional[ModelStatus] = None
    deployed_at: Optional[datetime] = None
    notes: Optional[str] = None
    can_rollback: Optional[bool] = None


class ModelVersionResponse(ModelVersionBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ModelVersionListResponse(BaseModel):
    items: list[ModelVersionResponse]
    total: int
    page: int
    size: int
    pages: int


class ModelVersionActivateResponse(BaseModel):
    id: UUID
    status: ModelStatus
    message: str
