from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.data_pipeline import DataPipeline


class DataPipelineRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_list(
        self,
        page: int = 1,
        size: int = 20,
        status: str | None = None,
    ) -> tuple[list[DataPipeline], int]:
        stmt = select(DataPipeline)
        count_stmt = select(func.count(DataPipeline.id))

        if status:
            stmt = stmt.where(DataPipeline.status == status)
            count_stmt = count_stmt.where(DataPipeline.status == status)

        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt = (
            stmt.order_by(DataPipeline.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        items = list((await self.session.execute(stmt)).scalars().all())

        return items, total

    async def get_by_id(self, id: UUID) -> DataPipeline | None:
        result = await self.session.execute(
            select(DataPipeline).where(DataPipeline.id == id)
        )
        return result.scalar_one_or_none()

    async def create(self, obj: DataPipeline) -> DataPipeline:
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: DataPipeline, data: dict) -> DataPipeline:
        for key, value in data.items():
            if value is not None:
                setattr(obj, key, value)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj: DataPipeline) -> None:
        await self.session.delete(obj)
        await self.session.flush()

    async def trigger(self, obj: DataPipeline) -> DataPipeline:
        from src.models.data_pipeline import PipelineStatus

        obj.status = PipelineStatus.syncing
        await self.session.flush()
        await self.session.refresh(obj)
        return obj
