from datetime import date
from enum import Enum
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import TimestampedRead


class EquipmentType(str, Enum):
    PUMP = "pump"
    COMPRESSOR = "compressor"
    HEAT_EXCHANGER = "heat_exchanger"
    VESSEL = "vessel"
    TANK = "tank"
    VALVE = "valve"
    REACTOR = "reactor"
    FURNACE = "furnace"
    INSTRUMENT = "instrument"


class EquipmentStatus(str, Enum):
    OPERATIONAL = "operational"
    UNDER_MAINTENANCE = "under_maintenance"
    STANDBY = "standby"
    DECOMMISSIONED = "decommissioned"


class Criticality(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    SAFETY_CRITICAL = "safety_critical"


class EquipmentBase(BaseModel):
    zone_id: UUID
    tag_number: str
    name: str
    equipment_type: EquipmentType
    manufacturer: str | None = None
    model_number: str | None = None
    installation_date: date | None = None
    status: EquipmentStatus = EquipmentStatus.OPERATIONAL
    criticality: Criticality | None = None


class EquipmentCreate(EquipmentBase):
    pass


class EquipmentUpdate(BaseModel):
    zone_id: UUID | None = None
    tag_number: str | None = None
    name: str | None = None
    equipment_type: EquipmentType | None = None
    manufacturer: str | None = None
    model_number: str | None = None
    installation_date: date | None = None
    status: EquipmentStatus | None = None
    criticality: Criticality | None = None


class EquipmentRead(EquipmentBase, TimestampedRead):
    pass
