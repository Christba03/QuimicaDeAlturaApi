import math
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.drug_reference import DrugReference
from src.repositories.drug_reference_repository import DrugReferenceRepository
from src.schemas.drug_reference import (
    DrugReferenceCreate,
    DrugReferenceListResponse,
    DrugReferenceUpdate,
)

logger = structlog.get_logger()


class DrugReferenceService:
    def __init__(self, session: AsyncSession):
        self.repo = DrugReferenceRepository(session)
        self.session = session

    async def list_drug_references(
        self,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
    ) -> DrugReferenceListResponse:
        items, total = await self.repo.get_list(
            page=page,
            size=size,
            search=search,
        )
        pages = math.ceil(total / size) if total > 0 else 0
        return DrugReferenceListResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    async def get_drug_reference(self, id: UUID) -> DrugReference | None:
        return await self.repo.get_by_id(id)

    async def create_drug_reference(self, data: DrugReferenceCreate) -> DrugReference:
        reference = DrugReference(**data.model_dump())
        reference = await self.repo.create(reference)
        await self.session.commit()
        logger.info("drug_reference_created", reference_id=str(reference.id))
        return reference

    async def update_drug_reference(
        self, id: UUID, data: DrugReferenceUpdate
    ) -> DrugReference | None:
        reference = await self.repo.get_by_id(id)
        if not reference:
            return None

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return reference

        reference = await self.repo.update(reference, update_data)
        await self.session.commit()
        logger.info("drug_reference_updated", reference_id=str(id))
        return reference

    async def delete_drug_reference(self, id: UUID) -> bool:
        reference = await self.repo.get_by_id(id)
        if not reference:
            return False
        await self.repo.delete(reference)
        await self.session.commit()
        logger.info("drug_reference_deleted", reference_id=str(id))
        return True
