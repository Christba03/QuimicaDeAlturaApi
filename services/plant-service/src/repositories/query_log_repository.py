from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.query_log import QueryLog


class QueryLogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_list(
        self,
        page: int = 1,
        size: int = 20,
        flagged: bool | None = None,
    ) -> tuple[list[QueryLog], int]:
        stmt = select(QueryLog)
        count_stmt = select(func.count(QueryLog.id))

        if flagged is not None:
            stmt = stmt.where(QueryLog.flagged == flagged)
            count_stmt = count_stmt.where(QueryLog.flagged == flagged)

        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt = (
            stmt.order_by(QueryLog.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        items = list((await self.session.execute(stmt)).scalars().all())

        return items, total

    async def get_by_id(self, id: UUID) -> QueryLog | None:
        result = await self.session.execute(
            select(QueryLog).where(QueryLog.id == id)
        )
        return result.scalar_one_or_none()

    async def update(self, obj: QueryLog, data: dict) -> QueryLog:
        for key, value in data.items():
            if value is not None:
                setattr(obj, key, value)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj: QueryLog) -> None:
        await self.session.delete(obj)
        await self.session.flush()
