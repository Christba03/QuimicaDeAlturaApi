import math
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.query_log import QueryLog
from src.repositories.query_log_repository import QueryLogRepository
from src.schemas.query_log import (
    QueryLogFlagUpdate,
    QueryLogListResponse,
)

logger = structlog.get_logger()


class QueryLogService:
    def __init__(self, session: AsyncSession):
        self.repo = QueryLogRepository(session)
        self.session = session

    async def list_query_logs(
        self,
        page: int = 1,
        size: int = 20,
        flagged: bool | None = None,
    ) -> QueryLogListResponse:
        items, total = await self.repo.get_list(
            page=page,
            size=size,
            flagged=flagged,
        )
        pages = math.ceil(total / size) if total > 0 else 0
        return QueryLogListResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    async def get_query_log(self, id: UUID) -> QueryLog | None:
        return await self.repo.get_by_id(id)

    async def update_query_log(
        self, id: UUID, data: QueryLogFlagUpdate
    ) -> QueryLog | None:
        log = await self.repo.get_by_id(id)
        if not log:
            return None

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return log

        log = await self.repo.update(log, update_data)
        await self.session.commit()
        logger.info("query_log_updated", log_id=str(id))
        return log

    async def delete_query_log(self, id: UUID) -> bool:
        log = await self.repo.get_by_id(id)
        if not log:
            return False
        await self.repo.delete(log)
        await self.session.commit()
        logger.info("query_log_deleted", log_id=str(id))
        return True
