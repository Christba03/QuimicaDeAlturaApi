from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.events import EventPublisher
from src.models.plant import Plant, PlantStatus
from src.repositories.plant_repository import PlantRepository

logger = structlog.get_logger()


class VerificationService:
    def __init__(
        self,
        session: AsyncSession,
        events: EventPublisher | None = None,
    ):
        self.repo = PlantRepository(session)
        self.session = session
        self.events = events

    async def submit_for_review(self, plant_id: UUID) -> Plant | None:
        plant = await self.repo.get_by_id(plant_id)
        if not plant:
            return None

        if plant.status != PlantStatus.DRAFT:
            raise ValueError(
                f"Plant must be in DRAFT status to submit for review. "
                f"Current status: {plant.status.value}"
            )

        plant = await self.repo.update_status(plant, PlantStatus.PENDING_REVIEW)
        await self.session.commit()

        if self.events:
            await self.events.publish(
                "plant.submitted_for_review",
                {"plant_id": str(plant.id), "scientific_name": plant.scientific_name},
            )

        logger.info("plant_submitted_for_review", plant_id=str(plant_id))
        return plant

    async def approve(
        self, plant_id: UUID, reviewer_id: UUID
    ) -> Plant | None:
        plant = await self.repo.get_by_id(plant_id)
        if not plant:
            return None

        if plant.status != PlantStatus.PENDING_REVIEW:
            raise ValueError(
                f"Plant must be in PENDING_REVIEW status to approve. "
                f"Current status: {plant.status.value}"
            )

        plant = await self.repo.update_status(
            plant, PlantStatus.VERIFIED, reviewed_by=reviewer_id
        )
        await self.session.commit()

        if self.events:
            await self.events.publish(
                "plant.approved",
                {
                    "plant_id": str(plant.id),
                    "reviewer_id": str(reviewer_id),
                },
            )

        logger.info(
            "plant_approved",
            plant_id=str(plant_id),
            reviewer_id=str(reviewer_id),
        )
        return plant

    async def reject(
        self,
        plant_id: UUID,
        reviewer_id: UUID,
        reason: str | None = None,
    ) -> Plant | None:
        plant = await self.repo.get_by_id(plant_id)
        if not plant:
            return None

        if plant.status != PlantStatus.PENDING_REVIEW:
            raise ValueError(
                f"Plant must be in PENDING_REVIEW status to reject. "
                f"Current status: {plant.status.value}"
            )

        plant = await self.repo.update_status(
            plant, PlantStatus.REJECTED, reviewed_by=reviewer_id
        )
        await self.session.commit()

        if self.events:
            await self.events.publish(
                "plant.rejected",
                {
                    "plant_id": str(plant.id),
                    "reviewer_id": str(reviewer_id),
                    "reason": reason,
                },
            )

        logger.info(
            "plant_rejected",
            plant_id=str(plant_id),
            reviewer_id=str(reviewer_id),
            reason=reason,
        )
        return plant

    async def revert_to_draft(self, plant_id: UUID) -> Plant | None:
        plant = await self.repo.get_by_id(plant_id)
        if not plant:
            return None

        if plant.status not in (PlantStatus.REJECTED, PlantStatus.PENDING_REVIEW):
            raise ValueError(
                f"Plant must be in REJECTED or PENDING_REVIEW status to revert. "
                f"Current status: {plant.status.value}"
            )

        plant = await self.repo.update_status(plant, PlantStatus.DRAFT)
        await self.session.commit()

        logger.info("plant_reverted_to_draft", plant_id=str(plant_id))
        return plant
