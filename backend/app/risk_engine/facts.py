"""
ZoneFacts: the one normalized, in-process shape every Rule is allowed to depend on. Rules
never touch the ORM or query the database directly — this is the seam that keeps every rule
unit-testable with a hand-built fixture and no mocking.

Plain frozen dataclasses, not Pydantic: this is internally computed data assembled fresh on
every evaluation pass, never serialized or round-tripped across a process boundary — unlike
app/plant_types/schema.py's Pydantic models, which validate externally-authored config.
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class EntityRef:
    """A pointer to the specific entity that made a rule fire — used both for confidence
    scoring (was the evidence trustworthy?) and as contributor metadata the frontend/future
    Knowledge Graph can use to deep-link back to the source record."""

    entity_type: str  # "sensor" | "equipment" | "permit" | "worker"
    entity_id: UUID
    label: str


@dataclass(frozen=True)
class SensorFact:
    sensor_id: UUID
    tag_number: str
    sensor_type: str
    unit_of_measure: str
    status: str  # active/inactive/under_calibration/faulted
    last_value: float | None
    last_reading_at: datetime | None
    normal_min: float | None
    normal_max: float | None
    warning_min: float | None
    warning_max: float | None
    critical_min: float | None
    critical_max: float | None
    sampling_interval_seconds: int
    equipment_id: UUID | None
    effective_band: str  # "normal" | "warning" | "critical" | "unknown"
    is_stale: bool


@dataclass(frozen=True)
class PermitFact:
    permit_id: UUID
    permit_number: str
    permit_type: str
    required_isolation: str | None
    equipment_id: UUID | None
    valid_until: datetime | None


@dataclass(frozen=True)
class EquipmentFact:
    equipment_id: UUID
    tag_number: str
    equipment_type: str
    status: str  # operational/under_maintenance/standby/decommissioned
    criticality: str | None  # low/medium/high/safety_critical/None


@dataclass(frozen=True)
class WorkerPresenceEntry:
    worker_id: UUID
    employee_id: str
    role: str


_CRITICALITY_RANK = {"low": 0, "medium": 1, "high": 2, "safety_critical": 3}


@dataclass(frozen=True)
class ZoneFacts:
    zone_id: UUID
    zone_code: str
    zone_name: str
    zone_type: str
    zone_category: str
    emergency_shutdown_active: bool
    sensors: tuple[SensorFact, ...]
    active_permits: tuple[PermitFact, ...]  # status == "active" only
    equipment: tuple[EquipmentFact, ...]  # all equipment in the zone, any status
    workers_present: tuple[WorkerPresenceEntry, ...]  # current_zone_id == zone_id
    evaluated_at: datetime  # tz-aware UTC "now" used for this evaluation pass

    def sensors_of_type(self, sensor_type: str) -> tuple[SensorFact, ...]:
        return tuple(s for s in self.sensors if s.sensor_type == sensor_type)

    def has_active_permit_type(self, permit_type: str) -> bool:
        return any(p.permit_type == permit_type for p in self.active_permits)

    def active_permits_for_equipment(self, equipment_id: UUID) -> tuple[PermitFact, ...]:
        return tuple(p for p in self.active_permits if p.equipment_id == equipment_id)

    @property
    def highest_equipment_criticality(self) -> str | None:
        """Max criticality across all equipment in the zone, or None if the zone has no
        equipment or none carry a criticality rating. Shared derived fact so rules that care
        about "does this zone contain safety-critical gear" don't each recompute it."""
        ranked = [e.criticality for e in self.equipment if e.criticality is not None]
        if not ranked:
            return None
        return max(ranked, key=lambda c: _CRITICALITY_RANK.get(c, -1))
