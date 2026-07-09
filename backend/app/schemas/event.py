from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import TimestampedRead


class EventType(str, Enum):
    EQUIPMENT_STATUS_CHANGE = "equipment_status_change"
    PERMIT_ISSUED = "permit_issued"
    PERMIT_APPROVED = "permit_approved"
    PERMIT_CLOSED = "permit_closed"
    WORKER_CHECK_IN = "worker_check_in"
    WORKER_CHECK_OUT = "worker_check_out"
    MAINTENANCE_LOGGED = "maintenance_logged"
    GENERAL = "general"


class EventBase(BaseModel):
    zone_id: UUID | None = None
    equipment_id: UUID | None = None
    permit_id: UUID | None = None
    recorded_by_id: UUID | None = None
    event_type: EventType
    title: str
    description: str | None = None
    occurred_at: datetime


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    zone_id: UUID | None = None
    equipment_id: UUID | None = None
    permit_id: UUID | None = None
    recorded_by_id: UUID | None = None
    event_type: EventType | None = None
    title: str | None = None
    description: str | None = None
    occurred_at: datetime | None = None


class EventRead(EventBase, TimestampedRead):
    pass
