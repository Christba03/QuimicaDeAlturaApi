import math
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.image_log import ImageLog
from src.repositories.image_log_repository import ImageLogRepository
from src.schemas.image_log import (
    ImageLogListResponse,
    ImageLogUpdate,
)

logger = structlog.get_logger()


class ImageLogService:
    def __init__(self, session: AsyncSession):
        self.repo = ImageLogRepository(session)
        self.session = session

    async def list_image_logs(
        self,
        page: int = 1,
        size: int = 20,
        flagged: bool | None = None,
    ) -> ImageLogListResponse:
        items, total = await self.repo.get_list(
            page=page,
            size=size,
            flagged=flagged,
        )
        pages = math.ceil(total / size) if total > 0 else 0
        return ImageLogListResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    async def get_image_log(self, id: UUID) -> ImageLog | None:
        return await self.repo.get_by_id(id)

    async def update_image_log(
        self, id: UUID, data: ImageLogUpdate
    ) -> ImageLog | None:
        log = await self.repo.get_by_id(id)
        if not log:
            return None

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return log

        log = await self.repo.update(log, update_data)
        await self.session.commit()
        logger.info("image_log_updated", log_id=str(id))
        return log

    async def delete_image_log(self, id: UUID) -> bool:
        log = await self.repo.get_by_id(id)
        if not log:
            return False
        await self.repo.delete(log)
        await self.session.commit()
        logger.info("image_log_deleted", log_id=str(id))
        return True
