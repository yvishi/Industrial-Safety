from datetime import date
from enum import Enum
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import TimestampedRead


class EquipmentType(str, Enum):
    """Union of the asset vocabularies across supported plant types (see app/plant_types/)."""

    PUMP = "pump"
    FIRE_PUMP = "fire_pump"
    COMPRESSOR = "compressor"
    HEAT_EXCHANGER = "heat_exchanger"
    FIRED_HEATER = "fired_heater"
    BOILER = "boiler"
    DISTILLATION_COLUMN = "distillation_column"
    VESSEL = "vessel"
    TANK = "tank"
    CONTROL_VALVE = "control_valve"
    RELIEF_VALVE = "relief_valve"
    LOADING_ARM = "loading_arm"
    FLARE_STACK = "flare_stack"
    VACUUM_EJECTOR = "vacuum_ejector"
    GENERATOR = "generator"
    CONTROL_SYSTEM = "control_system"
    HVAC = "hvac"
    CRANE = "crane"


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
