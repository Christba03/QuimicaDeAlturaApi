from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.inference_job import InferenceJob


class InferenceJobRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_list(
        self,
        page: int = 1,
        size: int = 20,
        status: str | None = None,
        flagged: bool | None = None,
    ) -> tuple[list[InferenceJob], int]:
        stmt = select(InferenceJob)
        count_stmt = select(func.count(InferenceJob.id))

        if status:
            stmt = stmt.where(InferenceJob.status == status)
            count_stmt = count_stmt.where(InferenceJob.status == status)

        if flagged is not None:
            stmt = stmt.where(InferenceJob.flagged_for_review == flagged)
            count_stmt = count_stmt.where(InferenceJob.flagged_for_review == flagged)

        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt = (
            stmt.order_by(InferenceJob.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        items = list((await self.session.execute(stmt)).scalars().all())

        return items, total

    async def get_by_id(self, id: UUID) -> InferenceJob | None:
        result = await self.session.execute(
            select(InferenceJob).where(InferenceJob.id == id)
        )
        return result.scalar_one_or_none()

    async def create(self, obj: InferenceJob) -> InferenceJob:
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: InferenceJob, data: dict) -> InferenceJob:
        for key, value in data.items():
            if value is not None:
                setattr(obj, key, value)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj: InferenceJob) -> None:
        await self.session.delete(obj)
        await self.session.flush()
