from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.external_api import ExternalApi


class ExternalApiRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_list(
        self,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[ExternalApi], int]:
        stmt = select(ExternalApi)
        count_stmt = select(func.count(ExternalApi.id))

        if search:
            search_filter = ExternalApi.name.ilike(f"%{search}%")
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)

        if is_active is not None:
            stmt = stmt.where(ExternalApi.is_active == is_active)
            count_stmt = count_stmt.where(ExternalApi.is_active == is_active)

        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt = (
            stmt.order_by(ExternalApi.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        items = list((await self.session.execute(stmt)).scalars().all())

        return items, total

    async def get_by_id(self, id: UUID) -> ExternalApi | None:
        result = await self.session.execute(
            select(ExternalApi).where(ExternalApi.id == id)
        )
        return result.scalar_one_or_none()

    async def create(self, obj: ExternalApi) -> ExternalApi:
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: ExternalApi, data: dict) -> ExternalApi:
        for key, value in data.items():
            if value is not None:
                setattr(obj, key, value)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj: ExternalApi) -> None:
        await self.session.delete(obj)
        await self.session.flush()
