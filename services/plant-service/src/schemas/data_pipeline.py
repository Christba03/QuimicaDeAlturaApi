from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel

from src.models.data_pipeline import PipelineStatus


class DataPipelineBase(BaseModel):
    name: str
    source: Optional[str] = None
    last_sync: Optional[datetime] = None
    next_sync: Optional[datetime] = None
    records_synced: int = 0
    error_log: Optional[str] = None
    status: Optional[PipelineStatus] = PipelineStatus.idle


class DataPipelineCreate(DataPipelineBase):
    pass


class DataPipelineUpdate(BaseModel):
    name: Optional[str] = None
    source: Optional[str] = None
    last_sync: Optional[datetime] = None
    next_sync: Optional[datetime] = None
    records_synced: Optional[int] = None
    error_log: Optional[str] = None
    status: Optional[PipelineStatus] = None


class DataPipelineResponse(DataPipelineBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DataPipelineListResponse(BaseModel):
    items: list[DataPipelineResponse]
    total: int
    page: int
    size: int
    pages: int
