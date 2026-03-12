import math
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.regional_availability import RegionalAvailability
from src.repositories.regional_availability_repository import RegionalAvailabilityRepository
from src.schemas.regional_availability import (
    RegionalAvailabilityCreate,
    RegionalAvailabilityListResponse,
    RegionalAvailabilityUpdate,
)

logger = structlog.get_logger()


class RegionalAvailabilityService:
    def __init__(self, session: AsyncSession):
        self.repo = RegionalAvailabilityRepository(session)
        self.session = session

    async def list_regional_availability(
        self,
        page: int = 1,
        size: int = 20,
        state: str | None = None,
        region: str | None = None,
        abundance: str | None = None,
    ) -> RegionalAvailabilityListResponse:
        items, total = await self.repo.get_list(
            page=page,
            size=size,
            state=state,
            region=region,
            abundance=abundance,
        )
        pages = math.ceil(total / size) if total > 0 else 0
        return RegionalAvailabilityListResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    async def get_regional_availability(self, id: UUID) -> RegionalAvailability | None:
        return await self.repo.get_by_id(id)

    async def create_regional_availability(self, data: RegionalAvailabilityCreate) -> RegionalAvailability:
        record = RegionalAvailability(**data.model_dump())
        record = await self.repo.create(record)
        await self.session.commit()
        logger.info("regional_availability_created", record_id=str(record.id))
        return record

    async def update_regional_availability(
        self, id: UUID, data: RegionalAvailabilityUpdate
    ) -> RegionalAvailability | None:
        record = await self.repo.get_by_id(id)
        if not record:
            return None

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return record

        record = await self.repo.update(record, update_data)
        await self.session.commit()
        logger.info("regional_availability_updated", record_id=str(id))
        return record

    async def delete_regional_availability(self, id: UUID) -> bool:
        record = await self.repo.get_by_id(id)
        if not record:
            return False
        await self.repo.delete(record)
        await self.session.commit()
        logger.info("regional_availability_deleted", record_id=str(id))
        return True
