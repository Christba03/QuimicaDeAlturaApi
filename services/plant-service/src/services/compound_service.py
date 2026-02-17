import math
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.compound import ChemicalCompound, PlantCompound
from src.repositories.compound_repository import CompoundRepository
from src.schemas.compound import (
    CompoundCreate,
    CompoundListResponse,
    CompoundUpdate,
    PlantCompoundCreate,
)

logger = structlog.get_logger()


class CompoundService:
    def __init__(self, session: AsyncSession):
        self.repo = CompoundRepository(session)
        self.session = session

    async def create_compound(self, data: CompoundCreate) -> ChemicalCompound:
        compound = ChemicalCompound(**data.model_dump())
        compound = await self.repo.create(compound)
        await self.session.commit()
        logger.info("compound_created", compound_id=str(compound.id))
        return compound

    async def get_compound(self, compound_id: UUID) -> ChemicalCompound | None:
        return await self.repo.get_by_id(compound_id)

    async def list_compounds(
        self,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
        compound_class: str | None = None,
    ) -> CompoundListResponse:
        compounds, total = await self.repo.get_list(
            page=page, size=size, search=search, compound_class=compound_class
        )
        pages = math.ceil(total / size) if total > 0 else 0
        return CompoundListResponse(
            items=compounds,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    async def update_compound(
        self, compound_id: UUID, data: CompoundUpdate
    ) -> ChemicalCompound | None:
        compound = await self.repo.get_by_id(compound_id)
        if not compound:
            return None

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return compound

        compound = await self.repo.update(compound, update_data)
        await self.session.commit()
        logger.info("compound_updated", compound_id=str(compound_id))
        return compound

    async def delete_compound(self, compound_id: UUID) -> bool:
        compound = await self.repo.get_by_id(compound_id)
        if not compound:
            return False
        await self.repo.delete(compound)
        await self.session.commit()
        logger.info("compound_deleted", compound_id=str(compound_id))
        return True

    async def link_compound_to_plant(
        self, data: PlantCompoundCreate
    ) -> PlantCompound:
        link = PlantCompound(**data.model_dump())
        link = await self.repo.link_to_plant(link)
        await self.session.commit()
        logger.info(
            "compound_linked",
            plant_id=str(data.plant_id),
            compound_id=str(data.compound_id),
        )
        return link

    async def unlink_compound_from_plant(
        self, plant_id: UUID, compound_id: UUID
    ) -> None:
        await self.repo.unlink_from_plant(plant_id, compound_id)
        await self.session.commit()
        logger.info(
            "compound_unlinked",
            plant_id=str(plant_id),
            compound_id=str(compound_id),
        )

    async def get_plant_compounds(
        self, plant_id: UUID
    ) -> list[PlantCompound]:
        return await self.repo.get_compounds_for_plant(plant_id)
