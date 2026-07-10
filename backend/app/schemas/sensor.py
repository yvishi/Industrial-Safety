from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import ORMBase, TimestampedRead


class SensorType(str, Enum):
    """
    Union of the instrument vocabularies across supported plant types (see app/plant_types/).
    These are real industrial measurement types, not abstract categories — gas detection is
    split into the specific hazards (H2S, combustible gas / LEL, oxygen depletion).
    """

    TEMPERATURE = "temperature"
    PRESSURE = "pressure"
    FLOW = "flow"
    LEVEL = "level"
    H2S = "h2s"
    COMBUSTIBLE_GAS = "combustible_gas"
    OXYGEN = "oxygen"
    VIBRATION = "vibration"
    VALVE_POSITION = "valve_position"
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

    # Alarm bands in unit_of_measure; nullable per side because hazards are directional
    # (H2S alarms high, oxygen and fire-water pressure alarm low).
    normal_min: float | None = None
    normal_max: float | None = None
    warning_min: float | None = None
    warning_max: float | None = None
    critical_min: float | None = None
    critical_max: float | None = None
    sampling_interval_seconds: int = 5


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
    normal_min: float | None = None
    normal_max: float | None = None
    warning_min: float | None = None
    warning_max: float | None = None
    critical_min: float | None = None
    critical_max: float | None = None
    sampling_interval_seconds: int | None = None


class SensorRead(SensorBase, TimestampedRead):
    # Latest simulated reading — read-only through the API.
    last_value: float | None = None
    last_reading_at: datetime | None = None


class SensorReadingRead(ORMBase):
    id: UUID
    sensor_id: UUID
    value: float
    recorded_at: datetime
