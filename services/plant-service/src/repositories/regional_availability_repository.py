from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.regional_availability import RegionalAvailability


class RegionalAvailabilityRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_list(
        self,
        page: int = 1,
        size: int = 20,
        state: str | None = None,
        region: str | None = None,
        abundance: str | None = None,
    ) -> tuple[list[RegionalAvailability], int]:
        stmt = select(RegionalAvailability)
        count_stmt = select(func.count(RegionalAvailability.id))

        if state:
            state_filter = RegionalAvailability.state.ilike(f"%{state}%")
            stmt = stmt.where(state_filter)
            count_stmt = count_stmt.where(state_filter)

        if region:
            region_filter = RegionalAvailability.region.ilike(f"%{region}%")
            stmt = stmt.where(region_filter)
            count_stmt = count_stmt.where(region_filter)

        if abundance:
            stmt = stmt.where(RegionalAvailability.abundance == abundance)
            count_stmt = count_stmt.where(RegionalAvailability.abundance == abundance)

        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt = (
            stmt.order_by(RegionalAvailability.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        items = list((await self.session.execute(stmt)).scalars().all())

        return items, total

    async def get_by_id(self, id: UUID) -> RegionalAvailability | None:
        result = await self.session.execute(
            select(RegionalAvailability).where(RegionalAvailability.id == id)
        )
        return result.scalar_one_or_none()

    async def create(self, obj: RegionalAvailability) -> RegionalAvailability:
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: RegionalAvailability, data: dict) -> RegionalAvailability:
        for key, value in data.items():
            if value is not None:
                setattr(obj, key, value)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj: RegionalAvailability) -> None:
        await self.session.delete(obj)
        await self.session.flush()
