import math
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.ethnobotanical import EthnobotanicalRecord
from src.repositories.ethnobotanical_repository import EthnobotanicalRepository
from src.schemas.ethnobotanical import (
    EthnobotanicalCreate,
    EthnobotanicalListResponse,
    EthnobotanicalUpdate,
)

logger = structlog.get_logger()


class EthnobotanicalService:
    def __init__(self, session: AsyncSession):
        self.repo = EthnobotanicalRepository(session)
        self.session = session

    async def list_ethnobotanical(
        self,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
        evidence_level: str | None = None,
        region: str | None = None,
    ) -> EthnobotanicalListResponse:
        items, total = await self.repo.get_list(
            page=page,
            size=size,
            search=search,
            evidence_level=evidence_level,
            region=region,
        )
        pages = math.ceil(total / size) if total > 0 else 0
        return EthnobotanicalListResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    async def get_ethnobotanical(self, id: UUID) -> EthnobotanicalRecord | None:
        return await self.repo.get_by_id(id)

    async def create_ethnobotanical(self, data: EthnobotanicalCreate) -> EthnobotanicalRecord:
        record = EthnobotanicalRecord(**data.model_dump())
        record = await self.repo.create(record)
        await self.session.commit()
        logger.info("ethnobotanical_record_created", record_id=str(record.id))
        return record

    async def update_ethnobotanical(
        self, id: UUID, data: EthnobotanicalUpdate
    ) -> EthnobotanicalRecord | None:
        record = await self.repo.get_by_id(id)
        if not record:
            return None

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return record

        record = await self.repo.update(record, update_data)
        await self.session.commit()
        logger.info("ethnobotanical_record_updated", record_id=str(id))
        return record

    async def delete_ethnobotanical(self, id: UUID) -> bool:
        record = await self.repo.get_by_id(id)
        if not record:
            return False
        await self.repo.delete(record)
        await self.session.commit()
        logger.info("ethnobotanical_record_deleted", record_id=str(id))
        return True
