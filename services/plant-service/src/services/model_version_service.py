import math
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.model_version import ModelVersion
from src.repositories.model_version_repository import ModelVersionRepository
from src.schemas.model_version import (
    ModelVersionCreate,
    ModelVersionListResponse,
    ModelVersionUpdate,
)

logger = structlog.get_logger()


class ModelVersionService:
    def __init__(self, session: AsyncSession):
        self.repo = ModelVersionRepository(session)
        self.session = session

    async def list_versions(
        self,
        page: int = 1,
        size: int = 20,
        status: str | None = None,
    ) -> ModelVersionListResponse:
        items, total = await self.repo.get_list(
            page=page,
            size=size,
            status=status,
        )
        pages = math.ceil(total / size) if total > 0 else 0
        return ModelVersionListResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    async def get_version(self, id: UUID) -> ModelVersion | None:
        return await self.repo.get_by_id(id)

    async def create_version(self, data: ModelVersionCreate) -> ModelVersion:
        version = ModelVersion(**data.model_dump())
        version = await self.repo.create(version)
        await self.session.commit()
        logger.info("model_version_created", version_id=str(version.id))
        return version

    async def update_version(
        self, id: UUID, data: ModelVersionUpdate
    ) -> ModelVersion | None:
        version = await self.repo.get_by_id(id)
        if not version:
            return None

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return version

        version = await self.repo.update(version, update_data)
        await self.session.commit()
        logger.info("model_version_updated", version_id=str(id))
        return version

    async def delete_version(self, id: UUID) -> bool:
        version = await self.repo.get_by_id(id)
        if not version:
            return False
        await self.repo.delete(version)
        await self.session.commit()
        logger.info("model_version_deleted", version_id=str(id))
        return True

    async def activate_version(self, id: UUID) -> ModelVersion | None:
        version = await self.repo.get_by_id(id)
        if not version:
            return None
        version = await self.repo.activate(version)
        await self.session.commit()
        logger.info("model_version_activated", version_id=str(id))
        return version

    async def rollback_version(self, id: UUID) -> ModelVersion | None:
        version = await self.repo.get_by_id(id)
        if not version:
            return None
        version = await self.repo.rollback(version)
        await self.session.commit()
        logger.info("model_version_rolled_back", version_id=str(id))
        return version
