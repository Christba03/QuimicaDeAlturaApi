import math
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.inference_job import InferenceJob
from src.repositories.inference_job_repository import InferenceJobRepository
from src.schemas.inference_job import (
    InferenceJobCreate,
    InferenceJobListResponse,
    InferenceJobUpdate,
)

logger = structlog.get_logger()


class InferenceJobService:
    def __init__(self, session: AsyncSession):
        self.repo = InferenceJobRepository(session)
        self.session = session

    async def list_inference_jobs(
        self,
        page: int = 1,
        size: int = 20,
        status: str | None = None,
        flagged: bool | None = None,
    ) -> InferenceJobListResponse:
        items, total = await self.repo.get_list(
            page=page,
            size=size,
            status=status,
            flagged=flagged,
        )
        pages = math.ceil(total / size) if total > 0 else 0
        return InferenceJobListResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    async def get_inference_job(self, id: UUID) -> InferenceJob | None:
        return await self.repo.get_by_id(id)

    async def create_inference_job(self, data: InferenceJobCreate) -> InferenceJob:
        job = InferenceJob(**data.model_dump())
        job = await self.repo.create(job)
        await self.session.commit()
        logger.info("inference_job_created", job_id=str(job.id))
        return job

    async def update_inference_job(
        self, id: UUID, data: InferenceJobUpdate
    ) -> InferenceJob | None:
        job = await self.repo.get_by_id(id)
        if not job:
            return None

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return job

        job = await self.repo.update(job, update_data)
        await self.session.commit()
        logger.info("inference_job_updated", job_id=str(id))
        return job

    async def delete_inference_job(self, id: UUID) -> bool:
        job = await self.repo.get_by_id(id)
        if not job:
            return False
        await self.repo.delete(job)
        await self.session.commit()
        logger.info("inference_job_deleted", job_id=str(id))
        return True
