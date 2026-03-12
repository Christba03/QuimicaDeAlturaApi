import math
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.external_api import ExternalApi
from src.repositories.external_api_repository import ExternalApiRepository
from src.schemas.external_api import (
    ExternalApiCreate,
    ExternalApiListResponse,
    ExternalApiUpdate,
)

logger = structlog.get_logger()


class ExternalApiService:
    def __init__(self, session: AsyncSession):
        self.repo = ExternalApiRepository(session)
        self.session = session

    async def list_apis(
        self,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> ExternalApiListResponse:
        items, total = await self.repo.get_list(
            page=page,
            size=size,
            search=search,
            is_active=is_active,
        )
        pages = math.ceil(total / size) if total > 0 else 0
        return ExternalApiListResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    async def get_api(self, id: UUID) -> ExternalApi | None:
        return await self.repo.get_by_id(id)

    async def create_api(self, data: ExternalApiCreate) -> ExternalApi:
        api = ExternalApi(**data.model_dump())
        api = await self.repo.create(api)
        await self.session.commit()
        logger.info("external_api_created", api_id=str(api.id))
        return api

    async def update_api(
        self, id: UUID, data: ExternalApiUpdate
    ) -> ExternalApi | None:
        api = await self.repo.get_by_id(id)
        if not api:
            return None

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return api

        api = await self.repo.update(api, update_data)
        await self.session.commit()
        logger.info("external_api_updated", api_id=str(id))
        return api

    async def delete_api(self, id: UUID) -> bool:
        api = await self.repo.get_by_id(id)
        if not api:
            return False
        await self.repo.delete(api)
        await self.session.commit()
        logger.info("external_api_deleted", api_id=str(id))
        return True
