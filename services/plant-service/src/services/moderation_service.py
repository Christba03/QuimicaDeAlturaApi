import math
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.moderation import ModerationItem
from src.repositories.moderation_repository import ModerationRepository
from src.schemas.moderation import (
    ModerationCreate,
    ModerationListResponse,
    ModerationUpdate,
)

logger = structlog.get_logger()


class ModerationService:
    def __init__(self, session: AsyncSession):
        self.repo = ModerationRepository(session)
        self.session = session

    async def list_moderation_items(
        self,
        page: int = 1,
        size: int = 20,
        status: str | None = None,
    ) -> ModerationListResponse:
        items, total = await self.repo.get_list(
            page=page,
            size=size,
            status=status,
        )
        pages = math.ceil(total / size) if total > 0 else 0
        return ModerationListResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    async def get_moderation_item(self, id: UUID) -> ModerationItem | None:
        return await self.repo.get_by_id(id)

    async def create_moderation_item(self, data: ModerationCreate) -> ModerationItem:
        item = ModerationItem(**data.model_dump())
        item = await self.repo.create(item)
        await self.session.commit()
        logger.info("moderation_item_created", item_id=str(item.id))
        return item

    async def update_moderation_item(
        self, id: UUID, data: ModerationUpdate
    ) -> ModerationItem | None:
        item = await self.repo.get_by_id(id)
        if not item:
            return None

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return item

        item = await self.repo.update(item, update_data)
        await self.session.commit()
        logger.info("moderation_item_updated", item_id=str(id))
        return item

    async def delete_moderation_item(self, id: UUID) -> bool:
        item = await self.repo.get_by_id(id)
        if not item:
            return False
        await self.repo.delete(item)
        await self.session.commit()
        logger.info("moderation_item_deleted", item_id=str(id))
        return True

    async def approve_item(
        self, id: UUID, reviewer_id: UUID, notes: str | None = None
    ) -> ModerationItem | None:
        item = await self.repo.get_by_id(id)
        if not item:
            return None
        item = await self.repo.approve(item, reviewer_id=reviewer_id, notes=notes)
        await self.session.commit()
        logger.info("moderation_item_approved", item_id=str(id), reviewer_id=str(reviewer_id))
        return item

    async def reject_item(
        self, id: UUID, reviewer_id: UUID, notes: str | None = None
    ) -> ModerationItem | None:
        item = await self.repo.get_by_id(id)
        if not item:
            return None
        item = await self.repo.reject(item, reviewer_id=reviewer_id, notes=notes)
        await self.session.commit()
        logger.info("moderation_item_rejected", item_id=str(id), reviewer_id=str(reviewer_id))
        return item
