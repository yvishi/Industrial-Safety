from datetime import date
from enum import Enum
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import TimestampedRead


class SensorType(str, Enum):
    TEMPERATURE = "temperature"
    PRESSURE = "pressure"
    FLOW = "flow"
    LEVEL = "level"
    GAS_DETECTION = "gas_detection"
    VIBRATION = "vibration"
    SMOKE = "smoke"


class SensorStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNDER_CALIBRATION = "under_calibration"
    FAULTED = "faulted"


class SensorBase(BaseModel):
    zone_id: UUID
    equipment_id: UUID | None = None
    tag_number: str
    sensor_type: SensorType
    unit_of_measure: str
    installation_date: date | None = None
    status: SensorStatus = SensorStatus.ACTIVE


class SensorCreate(SensorBase):
    pass


class SensorUpdate(BaseModel):
    zone_id: UUID | None = None
    equipment_id: UUID | None = None
    tag_number: str | None = None
    sensor_type: SensorType | None = None
    unit_of_measure: str | None = None
    installation_date: date | None = None
    status: SensorStatus | None = None


class SensorRead(SensorBase, TimestampedRead):
    pass
