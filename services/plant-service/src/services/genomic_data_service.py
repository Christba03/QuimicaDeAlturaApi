import math
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.genomic_data import GenomicData
from src.repositories.genomic_data_repository import GenomicDataRepository
from src.schemas.genomic_data import (
    GenomicDataCreate,
    GenomicDataListResponse,
    GenomicDataUpdate,
)

logger = structlog.get_logger()


class GenomicDataService:
    def __init__(self, session: AsyncSession):
        self.repo = GenomicDataRepository(session)
        self.session = session

    async def list_genomic_data(
        self,
        page: int = 1,
        size: int = 20,
        species: str | None = None,
        status: str | None = None,
    ) -> GenomicDataListResponse:
        items, total = await self.repo.get_list(
            page=page,
            size=size,
            species=species,
            status=status,
        )
        pages = math.ceil(total / size) if total > 0 else 0
        return GenomicDataListResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    async def get_genomic_data(self, id: UUID) -> GenomicData | None:
        return await self.repo.get_by_id(id)

    async def create_genomic_data(self, data: GenomicDataCreate) -> GenomicData:
        record = GenomicData(**data.model_dump())
        record = await self.repo.create(record)
        await self.session.commit()
        logger.info("genomic_data_created", record_id=str(record.id))
        return record

    async def update_genomic_data(
        self, id: UUID, data: GenomicDataUpdate
    ) -> GenomicData | None:
        record = await self.repo.get_by_id(id)
        if not record:
            return None

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return record

        record = await self.repo.update(record, update_data)
        await self.session.commit()
        logger.info("genomic_data_updated", record_id=str(id))
        return record

    async def delete_genomic_data(self, id: UUID) -> bool:
        record = await self.repo.get_by_id(id)
        if not record:
            return False
        await self.repo.delete(record)
        await self.session.commit()
        logger.info("genomic_data_deleted", record_id=str(id))
        return True
