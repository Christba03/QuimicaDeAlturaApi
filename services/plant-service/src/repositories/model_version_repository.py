from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.model_version import ModelVersion


class ModelVersionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_list(
        self,
        page: int = 1,
        size: int = 20,
        status: str | None = None,
    ) -> tuple[list[ModelVersion], int]:
        stmt = select(ModelVersion)
        count_stmt = select(func.count(ModelVersion.id))

        if status:
            stmt = stmt.where(ModelVersion.status == status)
            count_stmt = count_stmt.where(ModelVersion.status == status)

        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt = (
            stmt.order_by(ModelVersion.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        items = list((await self.session.execute(stmt)).scalars().all())

        return items, total

    async def get_by_id(self, id: UUID) -> ModelVersion | None:
        result = await self.session.execute(
            select(ModelVersion).where(ModelVersion.id == id)
        )
        return result.scalar_one_or_none()

    async def create(self, obj: ModelVersion) -> ModelVersion:
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: ModelVersion, data: dict) -> ModelVersion:
        for key, value in data.items():
            if value is not None:
                setattr(obj, key, value)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj: ModelVersion) -> None:
        await self.session.delete(obj)
        await self.session.flush()

    async def activate(self, obj: ModelVersion) -> ModelVersion:
        from src.models.model_version import ModelStatus

        obj.status = ModelStatus.active
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def rollback(self, obj: ModelVersion) -> ModelVersion:
        from src.models.model_version import ModelStatus

        obj.status = ModelStatus.deprecated
        await self.session.flush()
        await self.session.refresh(obj)
        return obj
