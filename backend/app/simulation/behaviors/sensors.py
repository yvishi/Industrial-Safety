"""
Sensor telemetry behavior — plant-type-driven.

Each instrument's *operating ranges* come from its own database row (seeded from the plant
type's zone templates), and its *physics* (dynamics mode, reversion strength, noise, resting
point) from the plant type's sensor catalog. Nothing here knows it is simulating a refinery.

Three dynamics modes (see app.plant_types.schema.SensorDynamics):

- mean_reverting: wanders around a resting value inside the normal band and always comes home.
  Occasionally a controlled *excursion* ramps the target to just above the warning level,
  holds, then recovers.
- integrating: carries a slow fill/draw rate that occasionally reverses — bulk tank levels.
- equipment_coupled: follows the attached asset; nominal while it runs, decays toward zero
  when it stops. Alarm-band events are suppressed while the asset is down — the equipment
  event already tells that story, and a stopped pump's zero flow is not a process alarm.

Band crossings (warning/critical, high or low side) become events; raw readings never do.
Each sensor is only sampled when its own sampling interval has elapsed.
"""

import random
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from app.models.equipment import Equipment
from app.models.event import Event
from app.models.sensor import Sensor, SensorReading
from app.models.zone import Zone
from app.plant_types.schema import PlantTypeDefinition, SensorDynamics, SensorTypeSpec
from app.simulation.events import make_event

EXCURSION_RAMP_TICKS = 24  # ~2 min climb at 5 s updates
EXCURSION_HOLD_TICKS = 12  # ~1 min at peak
# Hysteresis: an alarm only clears once the value is back inside the normal band by this
# fraction of the normal span, so readings hovering on a threshold don't flap events.
RECOVERY_MARGIN_FRACTION = 0.05

_FALLBACK_SPEC = SensorTypeSpec(slug="_fallback", label="Reading", unit="")

_BAND_RANK = {"normal": 0, "warning": 1, "critical": 2}


@dataclass
class _Params:
    """Runtime physics for one instrument: DB ranges + plant-type catalog, resolved per tick."""

    dynamics: SensorDynamics
    baseline: float
    sigma: float
    theta: float
    hard_min: float
    hard_max: float
    excursion_probability: float
    normal_min: float
    normal_max: float
    warning_min: float | None
    warning_max: float | None
    critical_min: float | None
    critical_max: float | None

    @property
    def span(self) -> float:
        return self.normal_max - self.normal_min


@dataclass
class Excursion:
    peak: float
    ramp_ticks_left: int
    hold_ticks_left: int


class SensorBehavior:
    """Holds per-run excursion/band/rate state; the DB stays the source of truth for values."""

    def __init__(self, rng: random.Random) -> None:
        self.rng = rng
        self.excursions: dict[UUID, Excursion] = {}
        self.bands: dict[UUID, str] = {}
        self.fill_rates: dict[UUID, float] = {}

    def tick(
        self,
        sensors: list[Sensor],
        zones_by_id: dict[UUID, Zone],
        equipment_by_id: dict[UUID, Equipment],
        definition: PlantTypeDefinition,
        now: datetime,
    ) -> tuple[list[SensorReading], list[Event]]:
        readings: list[SensorReading] = []
        events: list[Event] = []

        for sensor in sensors:
            if sensor.status != "active":
                continue
            if not self._sample_due(sensor, now):
                continue

            params = self._resolve_params(sensor, definition)
            equipment_running = self._equipment_running(sensor, equipment_by_id)

            if sensor.last_value is None:
                value = params.baseline + self.rng.gauss(0, params.sigma)
            else:
                value = self._step(sensor, params, equipment_running)

            value = max(params.hard_min, min(params.hard_max, value))
            sensor.last_value = round(value, 2)
            sensor.last_reading_at = now
            readings.append(
                SensorReading(sensor_id=sensor.id, value=sensor.last_value, recorded_at=now)
            )

            event = self._check_band_crossing(sensor, params, equipment_running, zones_by_id, now)
            if event is not None:
                events.append(event)

        return readings, events

    def _sample_due(self, sensor: Sensor, now: datetime) -> bool:
        if sensor.last_reading_at is None:
            return True
        last = sensor.last_reading_at
        if last.tzinfo is None:
            # SQLite (tests) round-trips timestamps naive; they were stored as UTC.
            last = last.replace(tzinfo=timezone.utc)
        return (now - last).total_seconds() >= sensor.sampling_interval_seconds

    def _resolve_params(self, sensor: Sensor, definition: PlantTypeDefinition) -> _Params:
        spec = definition.sensor_types.get(sensor.sensor_type, _FALLBACK_SPEC)
        template = definition.sensor_template_by_tag(sensor.tag_number)

        normal_min = sensor.normal_min if sensor.normal_min is not None else 0.0
        normal_max = sensor.normal_max if sensor.normal_max is not None else normal_min + 100.0
        span = normal_max - normal_min

        low_bounds = [b for b in (normal_min, sensor.warning_min, sensor.critical_min) if b is not None]
        high_bounds = [b for b in (normal_max, sensor.warning_max, sensor.critical_max) if b is not None]
        hard_min = spec.hard_min if spec.hard_min is not None else min(low_bounds) - 0.25 * span
        hard_max = spec.hard_max if spec.hard_max is not None else max(high_bounds) + 0.25 * span

        dynamics = spec.dynamics
        excursion_probability = spec.excursion_probability
        if template is not None:
            if template.dynamics is not None:
                dynamics = template.dynamics
            if template.excursion_probability is not None:
                excursion_probability = template.excursion_probability

        return _Params(
            dynamics=dynamics,
            baseline=normal_min + spec.baseline_fraction * span,
            sigma=spec.noise_fraction * span,
            theta=spec.theta,
            hard_min=hard_min,
            hard_max=hard_max,
            excursion_probability=excursion_probability,
            normal_min=normal_min,
            normal_max=normal_max,
            warning_min=sensor.warning_min,
            warning_max=sensor.warning_max,
            critical_min=sensor.critical_min,
            critical_max=sensor.critical_max,
        )

    def _equipment_running(self, sensor: Sensor, equipment_by_id: dict[UUID, Equipment]) -> bool:
        if sensor.equipment_id is None:
            return True
        equipment = equipment_by_id.get(sensor.equipment_id)
        return equipment is None or equipment.status == "operational"

    def _step(self, sensor: Sensor, params: _Params, equipment_running: bool) -> float:
        if params.dynamics is SensorDynamics.INTEGRATING:
            return self._step_integrating(sensor, params)
        if params.dynamics is SensorDynamics.EQUIPMENT_COUPLED and not equipment_running:
            # Asset is down: decay briskly toward the physical floor with barely any noise.
            self.excursions.pop(sensor.id, None)
            return (
                sensor.last_value
                + (params.theta * 2.5) * (params.hard_min - sensor.last_value)
                + self.rng.gauss(0, params.sigma * 0.2)
            )
        return self._step_mean_reverting(sensor, params)

    def _step_mean_reverting(self, sensor: Sensor, params: _Params) -> float:
        excursion = self.excursions.get(sensor.id)

        if (
            excursion is None
            and params.warning_max is not None
            and self.rng.random() < params.excursion_probability
        ):
            excursion = Excursion(
                peak=params.warning_max * self.rng.uniform(1.02, 1.12),
                ramp_ticks_left=EXCURSION_RAMP_TICKS,
                hold_ticks_left=EXCURSION_HOLD_TICKS,
            )
            self.excursions[sensor.id] = excursion

        if excursion is not None:
            # During an excursion the reversion target is the peak, not the resting value.
            target = excursion.peak
            theta = params.theta * 1.5  # climb with intent
            if excursion.ramp_ticks_left > 0:
                excursion.ramp_ticks_left -= 1
            elif excursion.hold_ticks_left > 0:
                excursion.hold_ticks_left -= 1
            else:
                del self.excursions[sensor.id]
        else:
            target = params.baseline
            theta = params.theta

        return sensor.last_value + theta * (target - sensor.last_value) + self.rng.gauss(0, params.sigma)

    def _step_integrating(self, sensor: Sensor, params: _Params) -> float:
        rate = self.fill_rates.get(sensor.id)
        if rate is None or self.rng.random() < 0.02:
            # New transfer: pick a fresh fill/draw rate (fraction of span per update).
            rate = self.rng.choice((-1, 1)) * self.rng.uniform(0.002, 0.006) * params.span
        # Turn transfers around at the edges of the normal band — a full tank starts drawing.
        if sensor.last_value >= params.normal_max and rate > 0:
            rate = -abs(rate)
        elif sensor.last_value <= params.normal_min and rate < 0:
            rate = abs(rate)
        self.fill_rates[sensor.id] = rate
        return sensor.last_value + rate + self.rng.gauss(0, params.sigma * 0.5)

    def _band(self, value: float, params: _Params, margin: float = 0.0) -> str:
        if params.critical_max is not None and value >= params.critical_max - margin:
            return "critical"
        if params.critical_min is not None and value <= params.critical_min + margin:
            return "critical"
        if params.warning_max is not None and value >= params.warning_max - margin:
            return "warning"
        if params.warning_min is not None and value <= params.warning_min + margin:
            return "warning"
        return "normal"

    def _check_band_crossing(
        self,
        sensor: Sensor,
        params: _Params,
        equipment_running: bool,
        zones_by_id: dict[UUID, Zone],
        now: datetime,
    ) -> Event | None:
        if params.dynamics is SensorDynamics.EQUIPMENT_COUPLED and not equipment_running:
            # Expected consequence of the stopped asset, not a process alarm.
            self.bands.pop(sensor.id, None)
            return None

        previous = self.bands.get(sensor.id, "normal")
        current = self._band(sensor.last_value, params)

        if _BAND_RANK[current] > _BAND_RANK[previous]:
            self.bands[sensor.id] = current
            return self._alarm_event(sensor, params, current, zones_by_id, now)

        if current == "normal" and previous != "normal":
            # Only clear once comfortably back inside the normal band (hysteresis).
            margin = -RECOVERY_MARGIN_FRACTION * params.span
            if self._band(sensor.last_value, params, margin=margin) == "normal":
                self.bands[sensor.id] = "normal"
                return self._recovered_event(sensor, zones_by_id, now)
            return None

        self.bands[sensor.id] = current if current != "normal" else previous
        return None

    def _alarm_event(
        self,
        sensor: Sensor,
        params: _Params,
        band: str,
        zones_by_id: dict[UUID, Zone],
        now: datetime,
    ) -> Event:
        zone = zones_by_id.get(sensor.zone_id)
        zone_name = zone.name if zone else "unknown zone"
        value = sensor.last_value
        unit = sensor.unit_of_measure

        if band == "critical":
            low = params.critical_min is not None and value <= params.critical_min
            threshold = params.critical_min if low else params.critical_max
            title = f"Critical {'low' if low else 'high'} reading on {sensor.tag_number}"
            event_type = "sensor_critical"
        else:
            low = params.warning_min is not None and value <= params.warning_min
            threshold = params.warning_min if low else params.warning_max
            title = f"{sensor.tag_number} outside normal operating range"
            event_type = "sensor_warning"

        side = "below" if low else "above"
        return make_event(
            event_type,
            title,
            now,
            description=(
                f"{sensor.tag_number} read {value} {unit} in {zone_name}, {side} the "
                f"{threshold} {unit} {band} threshold."
            ),
            zone_id=sensor.zone_id,
            equipment_id=sensor.equipment_id,
        )

    def _recovered_event(
        self, sensor: Sensor, zones_by_id: dict[UUID, Zone], now: datetime
    ) -> Event:
        zone = zones_by_id.get(sensor.zone_id)
        zone_name = zone.name if zone else "unknown zone"
        return make_event(
            "sensor_recovered",
            f"{sensor.tag_number} back in normal operating range",
            now,
            description=(
                f"{sensor.tag_number} back at {sensor.last_value} {sensor.unit_of_measure} "
                f"in {zone_name}."
            ),
            zone_id=sensor.zone_id,
            equipment_id=sensor.equipment_id,
        )
