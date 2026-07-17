from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel

from app.risk_engine.config.schema import RiskLevel
from app.schemas.common import TimestampedRead


class IncidentStatus(str, Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentOrigin(str, Enum):
    SYSTEM_DETECTED = "system_detected"
    MANUAL = "manual"


class IncidentClassification(str, Enum):
    """Deliberately separate from RiskLevel: most system-detected episodes are
    operational_episode and resolve uneventfully. Only reportable_incident carries the
    root_cause + incident_severity requirement at close() — see IncidentSeverity."""

    OPERATIONAL_EPISODE = "operational_episode"
    NEAR_MISS = "near_miss"
    SAFETY_INCIDENT = "safety_incident"
    REPORTABLE_INCIDENT = "reportable_incident"


class IncidentSeverity(str, Enum):
    """Actual real-world impact, assessed by a human at close() — deliberately a different
    5-tier vocabulary from RiskLevel (low/moderate/high/critical) so the two axes never look
    like the same scale: a Critical-risk incident handled immediately with no damage may only
    be Minor impact. Never derived algorithmically."""

    NEGLIGIBLE = "negligible"
    MINOR = "minor"
    SERIOUS = "serious"
    MAJOR = "major"
    CATASTROPHIC = "catastrophic"


class IncidentRead(TimestampedRead):
    primary_zone_id: UUID
    zone_name: str
    affected_zone_ids: list[str]
    status: IncidentStatus
    origin: IncidentOrigin
    classification: IncidentClassification
    risk_severity_at_open: RiskLevel | None
    peak_risk_severity: RiskLevel | None
    incident_severity: IncidentSeverity | None
    title: str
    summary: str
    opened_at: datetime
    resolved_at: datetime | None
    closed_at: datetime | None
    root_cause: str | None
    corrective_actions: list[str]
    opened_by_id: UUID | None
    closed_by_id: UUID | None


class IncidentManualCreate(BaseModel):
    """The path for incidents the sensors never saw at all (e.g. a slip-and-fall) — no
    RiskAssessment/ZoneFacts exists behind these, so risk_severity_at_open/peak_risk_severity/
    opened_context_snapshot are left unset."""

    primary_zone_id: UUID
    title: str
    description: str
    classification: IncidentClassification = IncidentClassification.SAFETY_INCIDENT
    opened_by_id: UUID | None = None


class IncidentNoteCreate(BaseModel):
    note_text: str
    actor_id: UUID | None = None


class IncidentEscalateRequest(BaseModel):
    classification: IncidentClassification
    actor_id: UUID | None = None


class IncidentCloseRequest(BaseModel):
    incident_severity: IncidentSeverity | None = None
    root_cause: str | None = None
    corrective_actions: list[str] = []
    actor_id: UUID | None = None
