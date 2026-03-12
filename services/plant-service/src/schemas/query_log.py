from datetime import datetime
from uuid import UUID
from typing import Any, Optional

from pydantic import BaseModel


class QueryLogResponse(BaseModel):
    id: UUID
    query: str
    extracted_entities: Optional[list[Any]] = None
    ontology_mappings: Optional[list[Any]] = None
    plants_returned: Optional[list[Any]] = None
    confidence: Optional[float] = None
    flagged: bool
    user_id: Optional[UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class QueryLogFlagUpdate(BaseModel):
    flagged: bool


class QueryLogListResponse(BaseModel):
    items: list[QueryLogResponse]
    total: int
    page: int
    size: int
    pages: int
