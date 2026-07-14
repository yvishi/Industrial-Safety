"""
Assembles ZoneFacts snapshots by querying the database directly — the only place risk_engine
code touches the ORM. Mirrors app.services.state.StateService.get_plant_state()'s pattern:
one whole-plant select() per table, then partition the results by zone_id in Python, rather
than BaseRepository.list() (paginates — wrong tool here) or going through a service layer.

Band classification (_band) replicates app.simulation.behaviors.sensors.SensorBehavior._band()
but is deliberately stateless: it's a pure function of the sensor row's current value and
thresholds, recomputed fresh on every call. The simulator tracks a previous-band dict to apply
hysteresis so alarm *events* don't flap; the Risk Engine has no "previous evaluation" to
compare against and no events to debounce, so there is nothing to carry between calls.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models import Equipment, Permit, Sensor, Worker, Zone
from app.risk_engine.config.schema import RiskEngineConfig
from app.risk_engine.facts import (
    EquipmentFact,
    PermitFact,
    SensorFact,
    WorkerPresenceEntry,
    ZoneFacts,
)


def _band(sensor: Sensor) -> str:
    """Critical checked before warning; each side checked independently since bounds are
    directional and nullable (a sensor may only alarm high, only low, or both)."""
    value = sensor.last_value
    if sensor.critical_max is not None and value >= sensor.critical_max:
        return "critical"
    if sensor.critical_min is not None and value <= sensor.critical_min:
        return "critical"
    if sensor.warning_max is not None and value >= sensor.warning_max:
        return "warning"
    if sensor.warning_min is not None and value <= sensor.warning_min:
        return "warning"
    return "normal"


def _as_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        # SQLite (tests) round-trips timestamps naive; they were stored as UTC.
        return value.replace(tzinfo=timezone.utc)
    return value


def _sensor_fact(sensor: Sensor, evaluated_at: datetime, config: RiskEngineConfig) -> SensorFact:
    effective_band = (
        "unknown" if sensor.status != "active" or sensor.last_value is None else _band(sensor)
    )
    is_stale = (
        sensor.last_reading_at is None
        or (evaluated_at - _as_aware_utc(sensor.last_reading_at)).total_seconds()
        > config.staleness.stale_multiplier * sensor.sampling_interval_seconds
    )
    return SensorFact(
        sensor_id=sensor.id,
        tag_number=sensor.tag_number,
        sensor_type=sensor.sensor_type,
        unit_of_measure=sensor.unit_of_measure,
        status=sensor.status,
        last_value=sensor.last_value,
        last_reading_at=sensor.last_reading_at,
        normal_min=sensor.normal_min,
        normal_max=sensor.normal_max,
        warning_min=sensor.warning_min,
        warning_max=sensor.warning_max,
        critical_min=sensor.critical_min,
        critical_max=sensor.critical_max,
        sampling_interval_seconds=sensor.sampling_interval_seconds,
        equipment_id=sensor.equipment_id,
        effective_band=effective_band,
        is_stale=is_stale,
    )


def _permit_fact(permit: Permit) -> PermitFact:
    return PermitFact(
        permit_id=permit.id,
        permit_number=permit.permit_number,
        permit_type=permit.permit_type,
        required_isolation=permit.required_isolation,
        equipment_id=permit.equipment_id,
        valid_until=permit.valid_until,
    )


def _equipment_fact(equipment: Equipment) -> EquipmentFact:
    return EquipmentFact(
        equipment_id=equipment.id,
        tag_number=equipment.tag_number,
        equipment_type=equipment.equipment_type,
        status=equipment.status,
        criticality=equipment.criticality,
    )


def _worker_entry(worker: Worker) -> WorkerPresenceEntry:
    return WorkerPresenceEntry(worker_id=worker.id, employee_id=worker.employee_id, role=worker.role)


def _zone_facts(
    zone: Zone,
    sensors: list[Sensor],
    active_permits: list[Permit],
    equipment: list[Equipment],
    workers: list[Worker],
    evaluated_at: datetime,
    config: RiskEngineConfig,
) -> ZoneFacts:
    return ZoneFacts(
        zone_id=zone.id,
        zone_code=zone.code,
        zone_name=zone.name,
        zone_type=zone.zone_type,
        zone_category=zone.zone_category,
        emergency_shutdown_active=zone.emergency_shutdown_active,
        sensors=tuple(_sensor_fact(s, evaluated_at, config) for s in sensors),
        active_permits=tuple(_permit_fact(p) for p in active_permits),
        equipment=tuple(_equipment_fact(e) for e in equipment),
        workers_present=tuple(_worker_entry(w) for w in workers),
        evaluated_at=evaluated_at,
    )


class ZoneFactsBuilder:
    """Builds ZoneFacts snapshots for the Risk Engine. Read-only."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def build_for_plant(self, config: RiskEngineConfig) -> dict[UUID, ZoneFacts]:
        evaluated_at = datetime.now(timezone.utc)

        zones = (await self.session.execute(select(Zone))).scalars().all()
        sensors = (await self.session.execute(select(Sensor))).scalars().all()
        active_permits = (
            (await self.session.execute(select(Permit).where(Permit.status == "active")))
            .scalars()
            .all()
        )
        equipment = (await self.session.execute(select(Equipment))).scalars().all()
        workers = (await self.session.execute(select(Worker))).scalars().all()

        return {
            zone.id: _zone_facts(
                zone,
                [s for s in sensors if s.zone_id == zone.id],
                [p for p in active_permits if p.zone_id == zone.id],
                [e for e in equipment if e.zone_id == zone.id],
                [w for w in workers if w.current_zone_id == zone.id],
                evaluated_at,
                config,
            )
            for zone in zones
        }

    async def build_for_zone(self, zone_id: UUID, config: RiskEngineConfig) -> ZoneFacts:
        evaluated_at = datetime.now(timezone.utc)

        zone = (await self.session.execute(select(Zone).where(Zone.id == zone_id))).scalars().first()
        if zone is None:
            raise NotFoundError(f"Zone {zone_id} not found")

        sensors = (
            (await self.session.execute(select(Sensor).where(Sensor.zone_id == zone_id)))
            .scalars()
            .all()
        )
        active_permits = (
            (
                await self.session.execute(
                    select(Permit).where(Permit.zone_id == zone_id, Permit.status == "active")
                )
            )
            .scalars()
            .all()
        )
        equipment = (
            (await self.session.execute(select(Equipment).where(Equipment.zone_id == zone_id)))
            .scalars()
            .all()
        )
        workers = (
            (await self.session.execute(select(Worker).where(Worker.current_zone_id == zone_id)))
            .scalars()
            .all()
        )

        return _zone_facts(zone, sensors, active_permits, equipment, workers, evaluated_at, config)
