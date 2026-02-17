import uuid
from datetime import datetime
from typing import Sequence

from sqlalchemy import select, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.favorite import UserPlantFavorite
from src.models.usage_report import UserPlantUsageReport


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # ── Favorites ──────────────────────────────────────────────────────

    async def add_favorite(
        self,
        user_id: uuid.UUID,
        plant_id: uuid.UUID,
        notes: str | None = None,
        category: str | None = None,
    ) -> UserPlantFavorite:
        favorite = UserPlantFavorite(
            user_id=user_id,
            plant_id=plant_id,
            notes=notes,
            category=category,
        )
        self.session.add(favorite)
        await self.session.flush()
        return favorite

    async def remove_favorite(self, user_id: uuid.UUID, plant_id: uuid.UUID) -> bool:
        result = await self.session.execute(
            delete(UserPlantFavorite).where(
                and_(
                    UserPlantFavorite.user_id == user_id,
                    UserPlantFavorite.plant_id == plant_id,
                )
            )
        )
        return result.rowcount > 0  # type: ignore[union-attr]

    async def get_favorites(
        self,
        user_id: uuid.UUID,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[UserPlantFavorite], int]:
        count_q = select(func.count()).where(UserPlantFavorite.user_id == user_id)
        total = (await self.session.execute(count_q)).scalar_one()

        q = (
            select(UserPlantFavorite)
            .where(UserPlantFavorite.user_id == user_id)
            .order_by(UserPlantFavorite.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        rows = (await self.session.execute(q)).scalars().all()
        return rows, total

    async def is_favorite(self, user_id: uuid.UUID, plant_id: uuid.UUID) -> bool:
        q = select(func.count()).where(
            and_(
                UserPlantFavorite.user_id == user_id,
                UserPlantFavorite.plant_id == plant_id,
            )
        )
        count = (await self.session.execute(q)).scalar_one()
        return count > 0

    async def get_favorites_count(self, user_id: uuid.UUID) -> int:
        q = select(func.count()).where(UserPlantFavorite.user_id == user_id)
        return (await self.session.execute(q)).scalar_one()

    # ── Usage Reports ──────────────────────────────────────────────────

    async def create_usage_report(self, report: UserPlantUsageReport) -> UserPlantUsageReport:
        self.session.add(report)
        await self.session.flush()
        return report

    async def get_usage_report(
        self, report_id: uuid.UUID, user_id: uuid.UUID
    ) -> UserPlantUsageReport | None:
        q = select(UserPlantUsageReport).where(
            and_(
                UserPlantUsageReport.id == report_id,
                UserPlantUsageReport.user_id == user_id,
            )
        )
        return (await self.session.execute(q)).scalar_one_or_none()

    async def list_usage_reports(
        self,
        user_id: uuid.UUID,
        plant_id: uuid.UUID | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[UserPlantUsageReport], int]:
        conditions = [UserPlantUsageReport.user_id == user_id]
        if plant_id:
            conditions.append(UserPlantUsageReport.plant_id == plant_id)

        count_q = select(func.count()).where(and_(*conditions))
        total = (await self.session.execute(count_q)).scalar_one()

        q = (
            select(UserPlantUsageReport)
            .where(and_(*conditions))
            .order_by(UserPlantUsageReport.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        rows = (await self.session.execute(q)).scalars().all()
        return rows, total

    async def delete_usage_report(self, report_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        result = await self.session.execute(
            delete(UserPlantUsageReport).where(
                and_(
                    UserPlantUsageReport.id == report_id,
                    UserPlantUsageReport.user_id == user_id,
                )
            )
        )
        return result.rowcount > 0  # type: ignore[union-attr]

    async def get_reports_count(self, user_id: uuid.UUID) -> int:
        q = select(func.count()).where(UserPlantUsageReport.user_id == user_id)
        return (await self.session.execute(q)).scalar_one()

    # ── History (stored in Redis, but DB fallback for search history) ──

    async def get_plant_views_from_db(
        self,
        user_id: uuid.UUID,
        limit: int = 50,
    ) -> Sequence[UserPlantFavorite]:
        """Fallback: return recently favorited plants as a proxy for viewed plants."""
        q = (
            select(UserPlantFavorite)
            .where(UserPlantFavorite.user_id == user_id)
            .order_by(UserPlantFavorite.updated_at.desc())
            .limit(limit)
        )
        return (await self.session.execute(q)).scalars().all()
