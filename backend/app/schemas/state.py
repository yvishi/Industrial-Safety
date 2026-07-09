from datetime import datetime

from pydantic import BaseModel

from app.schemas.equipment import EquipmentRead
from app.schemas.event import EventRead
from app.schemas.permit import PermitRead
from app.schemas.plant import PlantRead
from app.schemas.sensor import SensorRead
from app.schemas.worker import WorkerRead
from app.schemas.zone import ZoneRead


class ZoneState(BaseModel):
    """One zone with everything currently in it — the frontend's per-zone building block."""

    zone: ZoneRead
    workers: list[WorkerRead]
    equipment: list[EquipmentRead]
    sensors: list[SensorRead]
    active_permit_count: int


class PlantState(BaseModel):
    """Aggregate snapshot of the whole plant; what the frontend polls."""

    plant: PlantRead
    generated_at: datetime
    zones: list[ZoneState]
    active_permits: list[PermitRead]
    recent_events: list[EventRead]
