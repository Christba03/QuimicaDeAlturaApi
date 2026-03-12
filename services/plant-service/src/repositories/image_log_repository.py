from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.image_log import ImageLog


class ImageLogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_list(
        self,
        page: int = 1,
        size: int = 20,
        flagged: bool | None = None,
    ) -> tuple[list[ImageLog], int]:
        stmt = select(ImageLog)
        count_stmt = select(func.count(ImageLog.id))

        if flagged is not None:
            stmt = stmt.where(ImageLog.flagged == flagged)
            count_stmt = count_stmt.where(ImageLog.flagged == flagged)

        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt = (
            stmt.order_by(ImageLog.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        items = list((await self.session.execute(stmt)).scalars().all())

        return items, total

    async def get_by_id(self, id: UUID) -> ImageLog | None:
        result = await self.session.execute(
            select(ImageLog).where(ImageLog.id == id)
        )
        return result.scalar_one_or_none()

    async def update(self, obj: ImageLog, data: dict) -> ImageLog:
        for key, value in data.items():
            if value is not None:
                setattr(obj, key, value)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj: ImageLog) -> None:
        await self.session.delete(obj)
        await self.session.flush()
