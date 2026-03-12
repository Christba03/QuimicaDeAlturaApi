import math
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.data_pipeline import DataPipeline
from src.repositories.data_pipeline_repository import DataPipelineRepository
from src.schemas.data_pipeline import (
    DataPipelineCreate,
    DataPipelineListResponse,
    DataPipelineUpdate,
)

logger = structlog.get_logger()


class DataPipelineService:
    def __init__(self, session: AsyncSession):
        self.repo = DataPipelineRepository(session)
        self.session = session

    async def list_pipelines(
        self,
        page: int = 1,
        size: int = 20,
        status: str | None = None,
    ) -> DataPipelineListResponse:
        items, total = await self.repo.get_list(
            page=page,
            size=size,
            status=status,
        )
        pages = math.ceil(total / size) if total > 0 else 0
        return DataPipelineListResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    async def get_pipeline(self, id: UUID) -> DataPipeline | None:
        return await self.repo.get_by_id(id)

    async def create_pipeline(self, data: DataPipelineCreate) -> DataPipeline:
        pipeline = DataPipeline(**data.model_dump())
        pipeline = await self.repo.create(pipeline)
        await self.session.commit()
        logger.info("data_pipeline_created", pipeline_id=str(pipeline.id))
        return pipeline

    async def update_pipeline(
        self, id: UUID, data: DataPipelineUpdate
    ) -> DataPipeline | None:
        pipeline = await self.repo.get_by_id(id)
        if not pipeline:
            return None

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return pipeline

        pipeline = await self.repo.update(pipeline, update_data)
        await self.session.commit()
        logger.info("data_pipeline_updated", pipeline_id=str(id))
        return pipeline

    async def delete_pipeline(self, id: UUID) -> bool:
        pipeline = await self.repo.get_by_id(id)
        if not pipeline:
            return False
        await self.repo.delete(pipeline)
        await self.session.commit()
        logger.info("data_pipeline_deleted", pipeline_id=str(id))
        return True

    async def trigger_pipeline(self, id: UUID) -> DataPipeline | None:
        pipeline = await self.repo.get_by_id(id)
        if not pipeline:
            return None
        pipeline = await self.repo.trigger(pipeline)
        await self.session.commit()
        logger.info("data_pipeline_triggered", pipeline_id=str(id))
        return pipeline
