from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.genomic_data import GenomicData


class GenomicDataRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_list(
        self,
        page: int = 1,
        size: int = 20,
        species: str | None = None,
        status: str | None = None,
    ) -> tuple[list[GenomicData], int]:
        stmt = select(GenomicData)
        count_stmt = select(func.count(GenomicData.id))

        if species:
            species_filter = GenomicData.species.ilike(f"%{species}%")
            stmt = stmt.where(species_filter)
            count_stmt = count_stmt.where(species_filter)

        if status:
            stmt = stmt.where(GenomicData.status == status)
            count_stmt = count_stmt.where(GenomicData.status == status)

        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt = (
            stmt.order_by(GenomicData.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        items = list((await self.session.execute(stmt)).scalars().all())

        return items, total

    async def get_by_id(self, id: UUID) -> GenomicData | None:
        result = await self.session.execute(
            select(GenomicData).where(GenomicData.id == id)
        )
        return result.scalar_one_or_none()

    async def create(self, obj: GenomicData) -> GenomicData:
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: GenomicData, data: dict) -> GenomicData:
        for key, value in data.items():
            if value is not None:
                setattr(obj, key, value)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj: GenomicData) -> None:
        await self.session.delete(obj)
        await self.session.flush()
