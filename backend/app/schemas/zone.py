from enum import Enum
from uuid import UUID

from pydantic import BaseModel

from app.plant_types.schema import ZoneCategory
from app.schemas.common import TimestampedRead

__all__ = ["ZoneCategory", "ZoneType", "ZoneBase", "ZoneCreate", "ZoneUpdate", "ZoneRead"]


class ZoneType(str, Enum):
    """
    Union of the zone vocabularies across supported plant types (see app/plant_types/) —
    mirrors the frontend's ZoneType union (src/features/plant/types/zone.ts) exactly.
    Adding an industry extends this enum; no migration needed (plain strings in the DB).
    """

    CONTROL_ROOM = "control_room"
    CRUDE_DISTILLATION = "crude_distillation"
    VACUUM_DISTILLATION = "vacuum_distillation"
    TANK_FARM = "tank_farm"
    PUMP_HOUSE = "pump_house"
    LOADING_BAY = "loading_bay"
    UTILITIES = "utilities"
    MAINTENANCE_WORKSHOP = "maintenance_workshop"
    FLARE_SYSTEM = "flare_system"
    FIRE_WATER = "fire_water"


class ZoneBase(BaseModel):
    plant_id: UUID
    code: str
    name: str
    zone_type: ZoneType
    zone_category: ZoneCategory = ZoneCategory.PROCESS
    description: str | None = None
    grid_row: int | None = None
    grid_col: int | None = None
    # Manual/external emergency-shutdown flag (stand-in for a future real ESD/DCS
    # integration). Toggling it is audit-logged by ZoneService as an Event.
    emergency_shutdown_active: bool = False


class ZoneCreate(ZoneBase):
    pass


class ZoneUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    zone_type: ZoneType | None = None
    zone_category: ZoneCategory | None = None
    description: str | None = None
    grid_row: int | None = None
    grid_col: int | None = None
    emergency_shutdown_active: bool | None = None


class ZoneRead(ZoneBase, TimestampedRead):
    pass
