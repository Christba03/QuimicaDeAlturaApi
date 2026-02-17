import json
import math
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.cache import PlantCache
from src.core.events import EventPublisher
from src.models.plant import Plant, PlantStatus, PlantVersion
from src.repositories.plant_repository import PlantRepository
from src.schemas.plant import PlantCreate, PlantListResponse, PlantUpdate

logger = structlog.get_logger()


class PlantService:
    def __init__(
        self,
        session: AsyncSession,
        cache: PlantCache | None = None,
        events: EventPublisher | None = None,
    ):
        self.repo = PlantRepository(session)
        self.session = session
        self.cache = cache
        self.events = events

    async def create_plant(
        self, data: PlantCreate, created_by: UUID | None = None
    ) -> Plant:
        plant = Plant(
            **data.model_dump(),
            created_by=created_by,
            status=PlantStatus.DRAFT,
        )
        plant = await self.repo.create(plant)
        await self.session.commit()

        # Create initial version
        await self._create_version(plant, "Initial creation", created_by)

        if self.events:
            await self.events.publish(
                "plant.created",
                {"plant_id": str(plant.id), "scientific_name": plant.scientific_name},
            )

        logger.info("plant_created", plant_id=str(plant.id))
        return plant

    async def get_plant(self, plant_id: UUID) -> Plant | None:
        if self.cache:
            cached = await self.cache.get_plant(plant_id)
            if cached:
                return cached

        plant = await self.repo.get_by_id(plant_id)

        if plant and self.cache:
            await self.cache.set_plant(plant)

        return plant

    async def list_plants(
        self,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
        family: str | None = None,
        status: PlantStatus | None = None,
    ) -> PlantListResponse:
        plants, total = await self.repo.get_list(
            page=page, size=size, search=search, family=family, status=status
        )
        pages = math.ceil(total / size) if total > 0 else 0
        return PlantListResponse(
            items=plants,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    async def update_plant(
        self,
        plant_id: UUID,
        data: PlantUpdate,
        changed_by: UUID | None = None,
    ) -> Plant | None:
        plant = await self.repo.get_by_id(plant_id)
        if not plant:
            return None

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return plant

        plant = await self.repo.update(plant, update_data)
        await self._create_version(
            plant,
            f"Updated fields: {', '.join(update_data.keys())}",
            changed_by,
        )
        await self.session.commit()

        if self.cache:
            await self.cache.invalidate_plant(plant_id)

        if self.events:
            await self.events.publish(
                "plant.updated",
                {"plant_id": str(plant.id), "fields": list(update_data.keys())},
            )

        logger.info("plant_updated", plant_id=str(plant_id))
        return plant

    async def delete_plant(self, plant_id: UUID) -> bool:
        plant = await self.repo.get_by_id(plant_id)
        if not plant:
            return False

        await self.repo.delete(plant)
        await self.session.commit()

        if self.cache:
            await self.cache.invalidate_plant(plant_id)

        if self.events:
            await self.events.publish(
                "plant.deleted", {"plant_id": str(plant_id)}
            )

        logger.info("plant_deleted", plant_id=str(plant_id))
        return True

    async def _create_version(
        self,
        plant: Plant,
        summary: str,
        changed_by: UUID | None = None,
    ) -> PlantVersion:
        version_number = await self.repo.get_latest_version_number(plant.id) + 1
        snapshot = json.dumps(
            {
                "scientific_name": plant.scientific_name,
                "common_name": plant.common_name,
                "family": plant.family,
                "genus": plant.genus,
                "species": plant.species,
                "description": plant.description,
                "status": plant.status.value if plant.status else None,
            }
        )
        version = PlantVersion(
            plant_id=plant.id,
            version_number=version_number,
            data_snapshot=snapshot,
            change_summary=summary,
            changed_by=changed_by,
        )
        version = await self.repo.create_version(version)
        await self.session.commit()
        return version
