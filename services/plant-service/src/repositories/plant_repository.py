import math
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.plant import Plant, PlantStatus, PlantVersion


class PlantRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, plant: Plant) -> Plant:
        self.session.add(plant)
        await self.session.flush()
        await self.session.refresh(plant)
        return plant

    async def get_by_id(self, plant_id: UUID) -> Plant | None:
        stmt = (
            select(Plant)
            .options(
                selectinload(Plant.compounds),
                selectinload(Plant.activities),
                selectinload(Plant.versions),
            )
            .where(Plant.id == plant_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_list(
        self,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
        family: str | None = None,
        status: PlantStatus | None = None,
    ) -> tuple[list[Plant], int]:
        stmt = select(Plant)
        count_stmt = select(func.count(Plant.id))

        if search:
            search_filter = or_(
                Plant.scientific_name.ilike(f"%{search}%"),
                Plant.common_name.ilike(f"%{search}%"),
            )
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)

        if family:
            stmt = stmt.where(Plant.family.ilike(f"%{family}%"))
            count_stmt = count_stmt.where(Plant.family.ilike(f"%{family}%"))

        if status:
            stmt = stmt.where(Plant.status == status)
            count_stmt = count_stmt.where(Plant.status == status)

        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = (
            stmt.order_by(Plant.scientific_name)
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await self.session.execute(stmt)
        plants = list(result.scalars().all())

        return plants, total

    async def update(self, plant: Plant, data: dict) -> Plant:
        for key, value in data.items():
            if value is not None:
                setattr(plant, key, value)
        await self.session.flush()
        await self.session.refresh(plant)
        return plant

    async def delete(self, plant: Plant) -> None:
        await self.session.delete(plant)
        await self.session.flush()

    async def create_version(self, version: PlantVersion) -> PlantVersion:
        self.session.add(version)
        await self.session.flush()
        return version

    async def get_latest_version_number(self, plant_id: UUID) -> int:
        stmt = (
            select(func.coalesce(func.max(PlantVersion.version_number), 0))
            .where(PlantVersion.plant_id == plant_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def update_status(
        self, plant: Plant, status: PlantStatus, reviewed_by: UUID | None = None
    ) -> Plant:
        plant.status = status
        if reviewed_by:
            plant.reviewed_by = reviewed_by
        await self.session.flush()
        await self.session.refresh(plant)
        return plant
