from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import TimestampedRead


class EventType(str, Enum):
    EQUIPMENT_STATUS_CHANGE = "equipment_status_change"
    EQUIPMENT_STARTED = "equipment_started"
    EQUIPMENT_STOPPED = "equipment_stopped"
    MAINTENANCE_STARTED = "maintenance_started"
    MAINTENANCE_COMPLETED = "maintenance_completed"
    PERMIT_ISSUED = "permit_issued"
    PERMIT_APPROVED = "permit_approved"
    PERMIT_ACTIVATED = "permit_activated"
    PERMIT_EXPIRED = "permit_expired"
    PERMIT_CLOSED = "permit_closed"
    WORKER_CHECK_IN = "worker_check_in"
    WORKER_CHECK_OUT = "worker_check_out"
    WORKER_ZONE_ENTRY = "worker_zone_entry"
    SENSOR_WARNING = "sensor_warning"
    SENSOR_CRITICAL = "sensor_critical"
    SENSOR_RECOVERED = "sensor_recovered"
    MAINTENANCE_LOGGED = "maintenance_logged"
    EMERGENCY_SHUTDOWN_ACTIVATED = "emergency_shutdown_activated"
    EMERGENCY_SHUTDOWN_CLEARED = "emergency_shutdown_cleared"
    RECOMMENDATION_ACKNOWLEDGED = "recommendation_acknowledged"
    RECOMMENDATION_RESOLVED = "recommendation_resolved"
    # --- Operational Timeline / Incident Manager additions (Rev. 2 architecture review) ---
    RISK_LEVEL_INCREASED = "risk_level_increased"
    RISK_LEVEL_DECREASED = "risk_level_decreased"
    RECOMMENDATION_CREATED = "recommendation_created"
    INCIDENT_OPENED = "incident_opened"
    INCIDENT_ESCALATED = "incident_escalated"
    INCIDENT_RESOLVED = "incident_resolved"
    INCIDENT_CLOSED = "incident_closed"
    INCIDENT_NOTE_ADDED = "incident_note_added"
    GENERAL = "general"


class ActorType(str, Enum):
    """Who caused this event to be recorded — a person acting through the API, or the
    platform itself (schedulers/engines). Internal system emitters never pass this field and
    get the "system" column default; the generic POST /events endpoint defaults to "operator"
    since a human is the one calling it."""

    SYSTEM = "system"
    OPERATOR = "operator"


class EventSeverity(str, Enum):
    INFO = "info"
    NOTICE = "notice"
    WARNING = "warning"
    CRITICAL = "critical"


# Every EventType member must appear here — enforced by a unit test (test_event_severity.py),
# not at import time, mirroring RuleWeightsConfig's own "checked by test, not at import" note.
# Severity is always derived server-side from event_type (see EventRepository.create); it is
# never an input a caller supplies.
EVENT_SEVERITY_MAP: dict[str, EventSeverity] = {
    EventType.GENERAL.value: EventSeverity.INFO,
    EventType.EQUIPMENT_STATUS_CHANGE.value: EventSeverity.NOTICE,
    EventType.EQUIPMENT_STARTED.value: EventSeverity.INFO,
    EventType.EQUIPMENT_STOPPED.value: EventSeverity.NOTICE,
    EventType.MAINTENANCE_STARTED.value: EventSeverity.INFO,
    EventType.MAINTENANCE_COMPLETED.value: EventSeverity.INFO,
    EventType.MAINTENANCE_LOGGED.value: EventSeverity.INFO,
    EventType.PERMIT_ISSUED.value: EventSeverity.INFO,
    EventType.PERMIT_APPROVED.value: EventSeverity.INFO,
    EventType.PERMIT_ACTIVATED.value: EventSeverity.NOTICE,
    EventType.PERMIT_EXPIRED.value: EventSeverity.WARNING,
    EventType.PERMIT_CLOSED.value: EventSeverity.INFO,
    EventType.WORKER_CHECK_IN.value: EventSeverity.INFO,
    EventType.WORKER_CHECK_OUT.value: EventSeverity.INFO,
    EventType.WORKER_ZONE_ENTRY.value: EventSeverity.INFO,
    EventType.SENSOR_WARNING.value: EventSeverity.WARNING,
    EventType.SENSOR_CRITICAL.value: EventSeverity.CRITICAL,
    EventType.SENSOR_RECOVERED.value: EventSeverity.INFO,
    EventType.EMERGENCY_SHUTDOWN_ACTIVATED.value: EventSeverity.CRITICAL,
    EventType.EMERGENCY_SHUTDOWN_CLEARED.value: EventSeverity.NOTICE,
    EventType.RECOMMENDATION_ACKNOWLEDGED.value: EventSeverity.NOTICE,
    EventType.RECOMMENDATION_RESOLVED.value: EventSeverity.NOTICE,
    EventType.RECOMMENDATION_CREATED.value: EventSeverity.WARNING,
    EventType.RISK_LEVEL_INCREASED.value: EventSeverity.WARNING,
    EventType.RISK_LEVEL_DECREASED.value: EventSeverity.NOTICE,
    EventType.INCIDENT_OPENED.value: EventSeverity.WARNING,
    EventType.INCIDENT_ESCALATED.value: EventSeverity.CRITICAL,
    EventType.INCIDENT_RESOLVED.value: EventSeverity.NOTICE,
    EventType.INCIDENT_CLOSED.value: EventSeverity.INFO,
    EventType.INCIDENT_NOTE_ADDED.value: EventSeverity.INFO,
}


class EventBase(BaseModel):
    zone_id: UUID | None = None
    equipment_id: UUID | None = None
    permit_id: UUID | None = None
    recorded_by_id: UUID | None = None
    recommendation_id: UUID | None = None
    incident_id: UUID | None = None
    actor_type: ActorType = ActorType.OPERATOR
    actor_id: UUID | None = None
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
    recommendation_id: UUID | None = None
    incident_id: UUID | None = None
    actor_type: ActorType | None = None
    actor_id: UUID | None = None
    event_type: EventType | None = None
    title: str | None = None
    description: str | None = None
    occurred_at: datetime | None = None


class EventRead(EventBase, TimestampedRead):
    risk_snapshot_id: UUID | None = None
    severity: EventSeverity
