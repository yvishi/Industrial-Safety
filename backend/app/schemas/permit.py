from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import TimestampedRead


class PermitType(str, Enum):
    HOT_WORK = "hot_work"
    CONFINED_SPACE = "confined_space"
    LINE_BREAKING = "line_breaking"
    LOCKOUT_TAGOUT = "lockout_tagout"
    WORKING_AT_HEIGHT = "working_at_height"
    EXCAVATION = "excavation"
    ELECTRICAL = "electrical"


class PermitStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    ACTIVE = "active"
    CLOSED = "closed"
    EXPIRED = "expired"
    REVOKED = "revoked"


class PermitBase(BaseModel):
    zone_id: UUID
    equipment_id: UUID | None = None
    permit_number: str
    permit_type: PermitType
    # Isolation standard demanded before the work may start (lockout_tagout, blind_purge_and_gas_test, ...).
    required_isolation: str | None = None
    description: str | None = None
    status: PermitStatus = PermitStatus.DRAFT
    requested_by_id: UUID
    approved_by_id: UUID | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None


class PermitCreate(PermitBase):
    pass


class PermitUpdate(BaseModel):
    zone_id: UUID | None = None
    equipment_id: UUID | None = None
    permit_number: str | None = None
    permit_type: PermitType | None = None
    required_isolation: str | None = None
    description: str | None = None
    status: PermitStatus | None = None
    approved_by_id: UUID | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None


class PermitRead(PermitBase, TimestampedRead):
    pass
