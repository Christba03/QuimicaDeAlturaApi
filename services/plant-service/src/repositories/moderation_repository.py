from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.moderation import ModerationItem


class ModerationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_list(
        self,
        page: int = 1,
        size: int = 20,
        status: str | None = None,
    ) -> tuple[list[ModerationItem], int]:
        stmt = select(ModerationItem)
        count_stmt = select(func.count(ModerationItem.id))

        if status:
            stmt = stmt.where(ModerationItem.status == status)
            count_stmt = count_stmt.where(ModerationItem.status == status)

        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt = (
            stmt.order_by(ModerationItem.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        items = list((await self.session.execute(stmt)).scalars().all())

        return items, total

    async def get_by_id(self, id: UUID) -> ModerationItem | None:
        result = await self.session.execute(
            select(ModerationItem).where(ModerationItem.id == id)
        )
        return result.scalar_one_or_none()

    async def create(self, obj: ModerationItem) -> ModerationItem:
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: ModerationItem, data: dict) -> ModerationItem:
        for key, value in data.items():
            if value is not None:
                setattr(obj, key, value)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj: ModerationItem) -> None:
        await self.session.delete(obj)
        await self.session.flush()

    async def approve(
        self,
        obj: ModerationItem,
        reviewer_id: UUID,
        notes: str | None,
    ) -> ModerationItem:
        from src.models.moderation import ModerationStatus

        obj.status = ModerationStatus.approved
        obj.reviewed_by = reviewer_id
        obj.reviewed_at = datetime.now(timezone.utc)
        if notes:
            obj.notes = notes
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def reject(
        self,
        obj: ModerationItem,
        reviewer_id: UUID,
        notes: str | None,
    ) -> ModerationItem:
        from src.models.moderation import ModerationStatus

        obj.status = ModerationStatus.rejected
        obj.reviewed_by = reviewer_id
        obj.reviewed_at = datetime.now(timezone.utc)
        if notes:
            obj.notes = notes
        await self.session.flush()
        await self.session.refresh(obj)
        return obj
