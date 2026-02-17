from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.compound import ChemicalCompound, PlantCompound


class CompoundRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, compound: ChemicalCompound) -> ChemicalCompound:
        self.session.add(compound)
        await self.session.flush()
        await self.session.refresh(compound)
        return compound

    async def get_by_id(self, compound_id: UUID) -> ChemicalCompound | None:
        stmt = select(ChemicalCompound).where(ChemicalCompound.id == compound_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_cas(self, cas_number: str) -> ChemicalCompound | None:
        stmt = select(ChemicalCompound).where(
            ChemicalCompound.cas_number == cas_number
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_list(
        self,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
        compound_class: str | None = None,
    ) -> tuple[list[ChemicalCompound], int]:
        stmt = select(ChemicalCompound)
        count_stmt = select(func.count(ChemicalCompound.id))

        if search:
            search_filter = ChemicalCompound.name.ilike(f"%{search}%")
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)

        if compound_class:
            stmt = stmt.where(
                ChemicalCompound.compound_class.ilike(f"%{compound_class}%")
            )
            count_stmt = count_stmt.where(
                ChemicalCompound.compound_class.ilike(f"%{compound_class}%")
            )

        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = (
            stmt.order_by(ChemicalCompound.name)
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await self.session.execute(stmt)
        compounds = list(result.scalars().all())

        return compounds, total

    async def update(self, compound: ChemicalCompound, data: dict) -> ChemicalCompound:
        for key, value in data.items():
            if value is not None:
                setattr(compound, key, value)
        await self.session.flush()
        await self.session.refresh(compound)
        return compound

    async def delete(self, compound: ChemicalCompound) -> None:
        await self.session.delete(compound)
        await self.session.flush()

    async def link_to_plant(self, link: PlantCompound) -> PlantCompound:
        self.session.add(link)
        await self.session.flush()
        await self.session.refresh(link)
        return link

    async def unlink_from_plant(
        self, plant_id: UUID, compound_id: UUID
    ) -> None:
        stmt = select(PlantCompound).where(
            PlantCompound.plant_id == plant_id,
            PlantCompound.compound_id == compound_id,
        )
        result = await self.session.execute(stmt)
        link = result.scalar_one_or_none()
        if link:
            await self.session.delete(link)
            await self.session.flush()

    async def get_compounds_for_plant(
        self, plant_id: UUID
    ) -> list[PlantCompound]:
        stmt = select(PlantCompound).where(PlantCompound.plant_id == plant_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
