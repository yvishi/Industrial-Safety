"""
Worker movement behavior.

Workers move only between grid-adjacent zones (the zone grid mirrors physical site layout),
with a homing bias back toward their primary assignment. Field roles roam; control-room
roles mostly stay put. Every move emits a worker_zone_entry event.
"""

import random
from datetime import datetime
from uuid import UUID

from app.models.event import Event
from app.models.worker import Worker
from app.models.zone import Zone
from app.simulation.events import make_event

FIELD_MOVE_PROBABILITY = 0.010  # per tick ≈ one move every ~8 min at 5s ticks
DESK_MOVE_PROBABILITY = 0.003  # managers/supervisors/safety leave the control room rarely
DESK_ROLES = {"plant_manager", "safety_officer", "shift_supervisor", "operations_director"}
MOBILE_STATUSES = {"active", "contractor"}


def _adjacent(a: Zone, b: Zone) -> bool:
    if a.grid_row is None or b.grid_row is None:
        return False
    return abs(a.grid_row - b.grid_row) + abs(a.grid_col - b.grid_col) == 1


def _distance(a: Zone, b: Zone) -> int:
    if a.grid_row is None or b.grid_row is None:
        return 99
    return abs(a.grid_row - b.grid_row) + abs(a.grid_col - b.grid_col)


class WorkerBehavior:
    def __init__(self, rng: random.Random) -> None:
        self.rng = rng

    def tick(
        self,
        workers: list[Worker],
        zones_by_id: dict[UUID, Zone],
        now: datetime,
    ) -> list[Event]:
        events: list[Event] = []
        zones = list(zones_by_id.values())

        for worker in workers:
            if worker.employment_status not in MOBILE_STATUSES:
                continue

            if worker.current_zone_id is None:
                worker.current_zone_id = worker.primary_zone_id
                continue

            current = zones_by_id.get(worker.current_zone_id)
            if current is None:
                continue

            probability = (
                DESK_MOVE_PROBABILITY if worker.role in DESK_ROLES else FIELD_MOVE_PROBABILITY
            )
            if self.rng.random() >= probability:
                continue

            neighbours = [z for z in zones if _adjacent(current, z)]
            if not neighbours:
                continue

            destination = self._choose_destination(worker, current, neighbours, zones_by_id)
            worker.current_zone_id = destination.id
            events.append(
                make_event(
                    "worker_zone_entry",
                    f"{worker.first_name} {worker.last_name} entered {destination.name}",
                    now,
                    zone_id=destination.id,
                    recorded_by_id=worker.id,
                )
            )

        return events

    def _choose_destination(
        self,
        worker: Worker,
        current: Zone,
        neighbours: list[Zone],
        zones_by_id: dict[UUID, Zone],
    ) -> Zone:
        primary = zones_by_id.get(worker.primary_zone_id) if worker.primary_zone_id else None
        if primary is None or primary.id == current.id:
            return self.rng.choice(neighbours)

        # Weight moves that bring the worker closer to home; going straight home weighs most.
        weights = []
        here = _distance(current, primary)
        for zone in neighbours:
            if zone.id == primary.id:
                weights.append(3.0)
            elif _distance(zone, primary) < here:
                weights.append(2.0)
            else:
                weights.append(1.0)
        return self.rng.choices(neighbours, weights=weights, k=1)[0]
