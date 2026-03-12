from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.drug_reference import DrugReference


class DrugReferenceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_list(
        self,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
    ) -> tuple[list[DrugReference], int]:
        stmt = select(DrugReference)
        count_stmt = select(func.count(DrugReference.id))

        if search:
            search_filter = DrugReference.drug_name.ilike(f"%{search}%")
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)

        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt = (
            stmt.order_by(DrugReference.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        items = list((await self.session.execute(stmt)).scalars().all())

        return items, total

    async def get_by_id(self, id: UUID) -> DrugReference | None:
        result = await self.session.execute(
            select(DrugReference).where(DrugReference.id == id)
        )
        return result.scalar_one_or_none()

    async def create(self, obj: DrugReference) -> DrugReference:
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: DrugReference, data: dict) -> DrugReference:
        for key, value in data.items():
            if value is not None:
                setattr(obj, key, value)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj: DrugReference) -> None:
        await self.session.delete(obj)
        await self.session.flush()
