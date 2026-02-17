from enum import Enum

from pydantic import BaseModel


class PlantEventType(str, Enum):
    PLANT_CREATED = "plant.created"
    PLANT_UPDATED = "plant.updated"
    PLANT_VERIFIED = "plant.verified"
    COMPOUND_ADDED = "compound.added"
    ACTIVITY_ADDED = "activity.added"


class PlantEvent(BaseModel):
    event_type: PlantEventType
    plant_id: int
    data: dict | None = None
