"""
Equipment lifecycle behavior.

Markov-style transitions between operational / standby / under_maintenance with dwell times
measured in tens of minutes, not seconds — industrial equipment doesn't flap. Safety-critical
assets (distillation column, reformer reactor, flare stack) never stop in the simulation:
the plant must always appear operational. Concurrent maintenance is capped so the site never
looks half-shut-down.
"""

import random
from datetime import datetime
from uuid import UUID

from app.models.equipment import Equipment
from app.models.event import Event
from app.models.zone import Zone
from app.simulation.events import make_event

# Per-tick probabilities at 5s ticks (approximate mean dwell in parentheses).
P_START_MAINTENANCE = 0.0008  # operational -> under_maintenance (~1 per 100 min per asset)
P_GO_STANDBY = 0.0006  # operational -> standby
P_LEAVE_STANDBY = 0.0040  # standby -> operational (~20 min standby)
P_FINISH_MAINTENANCE = 0.0035  # under_maintenance -> operational (~24 min job)
MAX_CONCURRENT_MAINTENANCE = 2


class EquipmentBehavior:
    def __init__(self, rng: random.Random) -> None:
        self.rng = rng

    def tick(
        self,
        equipment: list[Equipment],
        zones_by_id: dict[UUID, Zone],
        now: datetime,
    ) -> list[Event]:
        events: list[Event] = []
        in_maintenance = sum(1 for e in equipment if e.status == "under_maintenance")

        for asset in equipment:
            if asset.status == "decommissioned" or asset.criticality == "safety_critical":
                continue

            zone = zones_by_id.get(asset.zone_id)
            zone_id = zone.id if zone else None
            roll = self.rng.random()

            if asset.status == "operational":
                if roll < P_START_MAINTENANCE and in_maintenance < MAX_CONCURRENT_MAINTENANCE:
                    asset.status = "under_maintenance"
                    in_maintenance += 1
                    events.append(
                        make_event(
                            "maintenance_started",
                            f"Maintenance started on {asset.name} ({asset.tag_number})",
                            now,
                            zone_id=zone_id,
                            equipment_id=asset.id,
                        )
                    )
                elif roll < P_START_MAINTENANCE + P_GO_STANDBY:
                    asset.status = "standby"
                    events.append(
                        make_event(
                            "equipment_stopped",
                            f"{asset.name} ({asset.tag_number}) placed on standby",
                            now,
                            zone_id=zone_id,
                            equipment_id=asset.id,
                        )
                    )

            elif asset.status == "standby" and roll < P_LEAVE_STANDBY:
                asset.status = "operational"
                events.append(
                    make_event(
                        "equipment_started",
                        f"{asset.name} ({asset.tag_number}) started",
                        now,
                        zone_id=zone_id,
                        equipment_id=asset.id,
                    )
                )

            elif asset.status == "under_maintenance" and roll < P_FINISH_MAINTENANCE:
                asset.status = "operational"
                in_maintenance -= 1
                events.append(
                    make_event(
                        "maintenance_completed",
                        f"Maintenance completed on {asset.name} ({asset.tag_number})",
                        now,
                        zone_id=zone_id,
                        equipment_id=asset.id,
                    )
                )

        return events
