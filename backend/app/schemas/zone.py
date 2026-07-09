from enum import Enum
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import TimestampedRead


class ZoneType(str, Enum):
    """Mirrors the frontend's ZoneType union (src/features/plant/types/zone.ts) exactly."""

    CONTROL_ROOM = "control_room"
    PROCESSING_UNIT = "processing_unit"
    UTILITIES = "utilities"
    TANK_FARM = "tank_farm"
    PUMP_STATION = "pump_station"
    LOADING_RACK = "loading_rack"
    FLARE_STACK = "flare_stack"


class ZoneBase(BaseModel):
    plant_id: UUID
    code: str
    name: str
    zone_type: ZoneType
    description: str | None = None
    grid_row: int | None = None
    grid_col: int | None = None


class ZoneCreate(ZoneBase):
    pass


class ZoneUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    zone_type: ZoneType | None = None
    description: str | None = None
    grid_row: int | None = None
    grid_col: int | None = None


class ZoneRead(ZoneBase, TimestampedRead):
    pass
