"""
Sensor telemetry behavior.

Every tick each sensor takes a mean-reverting random-walk step toward its profile baseline —
values wander believably but always come home. Occasionally a sensor starts a controlled
*excursion*: over a couple of minutes its target ramps toward just above the warning level,
holds there briefly, then mean-reversion pulls it back down. Only warning-band crossings
become events; raw readings would drown the timeline.
"""

import random
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.models.event import Event
from app.models.sensor import Sensor, SensorReading
from app.models.zone import Zone
from app.simulation.events import make_event
from app.simulation.profiles import profile_for

# With ~23 sensors at a 5s tick this yields roughly one excursion per 8-10 minutes plant-wide.
EXCURSION_START_PROBABILITY = 0.0004
EXCURSION_RAMP_TICKS = 24  # ~2 min climb
EXCURSION_HOLD_TICKS = 12  # ~1 min at peak
RECOVERY_FRACTION = 0.85  # recovered once back below 85% of warning level

WARNING_EVENT_TYPE_BY_SENSOR = {
    "gas_detection": ("Gas concentration elevated", "sensor_warning"),
    "temperature": ("Temperature exceeded warning level", "sensor_warning"),
    "pressure": ("Pressure exceeded warning level", "sensor_warning"),
    "vibration": ("Vibration exceeded warning level", "sensor_warning"),
    "smoke": ("Smoke level elevated", "sensor_warning"),
    "flow": ("Flow rate outside normal band", "sensor_warning"),
    "level": ("Level approaching high limit", "sensor_warning"),
}


@dataclass
class Excursion:
    peak: float
    ramp_ticks_left: int
    hold_ticks_left: int


class SensorBehavior:
    """Holds per-run excursion/warning state; the DB stays the source of truth for values."""

    def __init__(self, rng: random.Random) -> None:
        self.rng = rng
        self.excursions: dict[UUID, Excursion] = {}
        self.in_warning: set[UUID] = set()

    def tick(
        self,
        sensors: list[Sensor],
        zones_by_id: dict[UUID, Zone],
        now: datetime,
    ) -> tuple[list[SensorReading], list[Event]]:
        readings: list[SensorReading] = []
        events: list[Event] = []

        for sensor in sensors:
            if sensor.status != "active":
                continue
            profile = profile_for(sensor.sensor_type)

            if sensor.last_value is None:
                # First tick for this sensor: start near baseline, no event.
                value = profile.baseline + self.rng.gauss(0, profile.sigma)
            else:
                value = self._step(sensor, profile)

            value = max(profile.minimum, min(profile.maximum, value))
            sensor.last_value = round(value, 2)
            sensor.last_reading_at = now
            readings.append(
                SensorReading(sensor_id=sensor.id, value=sensor.last_value, recorded_at=now)
            )

            event = self._check_warning_crossing(sensor, profile, zones_by_id, now)
            if event is not None:
                events.append(event)

        return readings, events

    def _step(self, sensor: Sensor, profile) -> float:
        excursion = self.excursions.get(sensor.id)

        if excursion is None and self.rng.random() < EXCURSION_START_PROBABILITY:
            excursion = Excursion(
                peak=profile.warning * self.rng.uniform(1.02, 1.15),
                ramp_ticks_left=EXCURSION_RAMP_TICKS,
                hold_ticks_left=EXCURSION_HOLD_TICKS,
            )
            self.excursions[sensor.id] = excursion

        if excursion is not None:
            # During an excursion the reversion target is the peak, not the baseline.
            target = excursion.peak
            theta = profile.theta * 1.5  # climb with intent
            if excursion.ramp_ticks_left > 0:
                excursion.ramp_ticks_left -= 1
            elif excursion.hold_ticks_left > 0:
                excursion.hold_ticks_left -= 1
            else:
                del self.excursions[sensor.id]
        else:
            target = profile.baseline
            theta = profile.theta

        return (
            sensor.last_value
            + theta * (target - sensor.last_value)
            + self.rng.gauss(0, profile.sigma)
        )

    def _check_warning_crossing(
        self,
        sensor: Sensor,
        profile,
        zones_by_id: dict[UUID, Zone],
        now: datetime,
    ) -> Event | None:
        zone = zones_by_id.get(sensor.zone_id)
        zone_name = zone.name if zone else "unknown zone"

        if sensor.last_value >= profile.warning and sensor.id not in self.in_warning:
            self.in_warning.add(sensor.id)
            title, event_type = WARNING_EVENT_TYPE_BY_SENSOR.get(
                sensor.sensor_type, ("Reading exceeded warning level", "sensor_warning")
            )
            return make_event(
                event_type,
                f"{title} ({sensor.tag_number})",
                now,
                description=(
                    f"{sensor.tag_number} read {sensor.last_value} {sensor.unit_of_measure} "
                    f"in {zone_name}, above the {profile.warning} {sensor.unit_of_measure} "
                    f"warning level."
                ),
                zone_id=sensor.zone_id,
                equipment_id=sensor.equipment_id,
            )

        if sensor.last_value < profile.warning * RECOVERY_FRACTION and sensor.id in self.in_warning:
            self.in_warning.discard(sensor.id)
            return make_event(
                "sensor_recovered",
                f"Reading returned to normal ({sensor.tag_number})",
                now,
                description=(
                    f"{sensor.tag_number} back at {sensor.last_value} {sensor.unit_of_measure} "
                    f"in {zone_name}."
                ),
                zone_id=sensor.zone_id,
                equipment_id=sensor.equipment_id,
            )

        return None
