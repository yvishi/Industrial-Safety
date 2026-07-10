from enum import Enum
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import TimestampedRead


class WorkerRole(str, Enum):
    PLANT_MANAGER = "plant_manager"
    SAFETY_OFFICER = "safety_officer"
    SHIFT_SUPERVISOR = "shift_supervisor"
    OPERATIONS_DIRECTOR = "operations_director"
    # Board operators run the units from the control room; outside/field operators walk them.
    CONSOLE_OPERATOR = "console_operator"
    FIELD_OPERATOR = "field_operator"
    MAINTENANCE_TECHNICIAN = "maintenance_technician"
    MAINTENANCE_PLANNER = "maintenance_planner"
    CONTRACTOR = "contractor"


class EmploymentStatus(str, Enum):
    ACTIVE = "active"
    ON_LEAVE = "on_leave"
    CONTRACTOR = "contractor"
    TERMINATED = "terminated"


class Shift(str, Enum):
    DAY = "day"
    NIGHT = "night"
    SWING = "swing"


class WorkerBase(BaseModel):
    employee_id: str
    first_name: str
    last_name: str
    role: WorkerRole
    employment_status: EmploymentStatus = EmploymentStatus.ACTIVE
    shift: Shift | None = None
    primary_zone_id: UUID | None = None


class WorkerCreate(WorkerBase):
    pass


class WorkerUpdate(BaseModel):
    employee_id: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    role: WorkerRole | None = None
    employment_status: EmploymentStatus | None = None
    shift: Shift | None = None
    primary_zone_id: UUID | None = None


class WorkerRead(WorkerBase, TimestampedRead):
    # Live location, written by the simulation engine — read-only through the API.
    current_zone_id: UUID | None = None
