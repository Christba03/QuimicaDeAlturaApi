import uuid

import structlog
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.usage_report import UserPlantUsageReport
from src.repositories.user_repository import UserRepository
from src.schemas.usage_report import (
    UsageReportCreate,
    UsageReportUpdate,
    UsageReportResponse,
    UsageReportListResponse,
)

logger = structlog.get_logger(__name__)


class UsageReportService:
    def __init__(self, session: AsyncSession, redis: aioredis.Redis):
        self.repo = UserRepository(session)
        self.redis = redis

    async def create_report(
        self, user_id: uuid.UUID, data: UsageReportCreate
    ) -> UsageReportResponse:
        report = UserPlantUsageReport(
            user_id=user_id,
            plant_id=data.plant_id,
            effectiveness=data.effectiveness,
            rating=data.rating,
            dosage=data.dosage,
            dosage_unit=data.dosage_unit,
            frequency=data.frequency,
            duration_days=data.duration_days,
            preparation_method=data.preparation_method,
            side_effects=data.side_effects,
            side_effects_list=data.side_effects_list,
            condition_treated=data.condition_treated,
            notes=data.notes,
            altitude_meters=data.altitude_meters,
        )
        saved = await self.repo.create_usage_report(report)
        logger.info(
            "Usage report created",
            user_id=str(user_id),
            plant_id=str(data.plant_id),
            effectiveness=data.effectiveness,
        )
        # Invalidate profile cache so reports_count updates
        await self.redis.delete(f"user:profile:{user_id}")
        return UsageReportResponse.model_validate(saved)

    async def get_report(
        self, report_id: uuid.UUID, user_id: uuid.UUID
    ) -> UsageReportResponse | None:
        report = await self.repo.get_usage_report(report_id, user_id)
        if report is None:
            return None
        return UsageReportResponse.model_validate(report)

    async def list_reports(
        self,
        user_id: uuid.UUID,
        plant_id: uuid.UUID | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> UsageReportListResponse:
        offset = (page - 1) * page_size
        rows, total = await self.repo.list_usage_reports(
            user_id=user_id,
            plant_id=plant_id,
            offset=offset,
            limit=page_size,
        )
        items = [UsageReportResponse.model_validate(r) for r in rows]
        return UsageReportListResponse(
            items=items, total=total, page=page, page_size=page_size
        )

    async def delete_report(self, report_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        deleted = await self.repo.delete_usage_report(report_id, user_id)
        if deleted:
            await self.redis.delete(f"user:profile:{user_id}")
            logger.info("Usage report deleted", report_id=str(report_id))
        return deleted
