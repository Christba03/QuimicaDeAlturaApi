from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.ethnobotanical import EthnobotanicalRecord


class EthnobotanicalRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_list(
        self,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
        evidence_level: str | None = None,
        region: str | None = None,
    ) -> tuple[list[EthnobotanicalRecord], int]:
        stmt = select(EthnobotanicalRecord)
        count_stmt = select(func.count(EthnobotanicalRecord.id))

        if search:
            search_filter = EthnobotanicalRecord.species.ilike(f"%{search}%")
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)

        if evidence_level:
            stmt = stmt.where(EthnobotanicalRecord.evidence_level == evidence_level)
            count_stmt = count_stmt.where(EthnobotanicalRecord.evidence_level == evidence_level)

        if region:
            region_filter = EthnobotanicalRecord.region.ilike(f"%{region}%")
            stmt = stmt.where(region_filter)
            count_stmt = count_stmt.where(region_filter)

        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt = (
            stmt.order_by(EthnobotanicalRecord.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        items = list((await self.session.execute(stmt)).scalars().all())

        return items, total

    async def get_by_id(self, id: UUID) -> EthnobotanicalRecord | None:
        result = await self.session.execute(
            select(EthnobotanicalRecord).where(EthnobotanicalRecord.id == id)
        )
        return result.scalar_one_or_none()

    async def create(self, obj: EthnobotanicalRecord) -> EthnobotanicalRecord:
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: EthnobotanicalRecord, data: dict) -> EthnobotanicalRecord:
        for key, value in data.items():
            if value is not None:
                setattr(obj, key, value)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj: EthnobotanicalRecord) -> None:
        await self.session.delete(obj)
        await self.session.flush()
