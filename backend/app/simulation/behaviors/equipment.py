"""
Equipment lifecycle behavior — plant-type-driven.

Markov-style transitions between operational / standby / under_maintenance, with per-type
probabilities from the plant type's equipment catalog (a loading arm idles between trucks;
a fired heater almost never stops). Safety-critical assets keep their seeded status — the
flare never goes out, and the diesel fire pump stays on standby where it belongs. Concurrent
maintenance is capped so the site never looks half-shut-down.

Installed spares (assets sharing a spare_group, e.g. crude charge pumps A/B) behave like a
real duty/standby pair: when the running unit goes down its spare auto-starts, and a unit
returning from maintenance goes to standby if its partner has already taken over.
"""

import random
from datetime import datetime
from uuid import UUID

from app.models.equipment import Equipment
from app.models.event import Event
from app.models.zone import Zone
from app.plant_types.schema import EquipmentBehavior as BehaviorSpec
from app.plant_types.schema import PlantTypeDefinition
from app.simulation.events import make_event

_DEFAULT_BEHAVIOR = BehaviorSpec()


class EquipmentBehavior:
    def __init__(self, rng: random.Random) -> None:
        self.rng = rng

    def tick(
        self,
        equipment: list[Equipment],
        zones_by_id: dict[UUID, Zone],
        definition: PlantTypeDefinition,
        now: datetime,
    ) -> tuple[list[Event], list[Equipment]]:
        """Returns (events, assets that entered maintenance this tick) — the permit behavior
        raises the matching work authorization for the latter."""
        events: list[Event] = []
        started_maintenance: list[Equipment] = []
        in_maintenance = sum(1 for e in equipment if e.status == "under_maintenance")
        max_maintenance = definition.tuning.max_concurrent_maintenance

        spare_groups = self._spare_groups(equipment, definition)

        for asset in equipment:
            if asset.status == "decommissioned" or asset.criticality == "safety_critical":
                continue

            spec = definition.equipment_types.get(asset.equipment_type)
            behavior = spec.behavior if spec is not None else _DEFAULT_BEHAVIOR
            roll = self.rng.random()

            if asset.status == "operational":
                if roll < behavior.p_start_maintenance and in_maintenance < max_maintenance:
                    asset.status = "under_maintenance"
                    in_maintenance += 1
                    started_maintenance.append(asset)
                    events.append(
                        make_event(
                            "maintenance_started",
                            f"Maintenance started on {asset.name} ({asset.tag_number})",
                            now,
                            zone_id=asset.zone_id,
                            equipment_id=asset.id,
                        )
                    )
                elif roll < behavior.p_start_maintenance + behavior.p_go_standby:
                    asset.status = "standby"
                    events.append(
                        make_event(
                            "equipment_stopped",
                            f"{asset.name} ({asset.tag_number}) placed on standby",
                            now,
                            zone_id=asset.zone_id,
                            equipment_id=asset.id,
                        )
                    )

            elif asset.status == "standby" and roll < behavior.p_leave_standby:
                asset.status = "operational"
                events.append(
                    make_event(
                        "equipment_started",
                        f"{asset.name} ({asset.tag_number}) started",
                        now,
                        zone_id=asset.zone_id,
                        equipment_id=asset.id,
                    )
                )

            elif asset.status == "under_maintenance" and roll < behavior.p_finish_maintenance:
                in_maintenance -= 1
                partners = spare_groups.get(self._group_key(asset, definition), [])
                if any(p.status == "operational" for p in partners if p.id != asset.id):
                    # The spare took over while this unit was down; return to standby.
                    asset.status = "standby"
                    title = f"{asset.name} ({asset.tag_number}) returned to standby after maintenance"
                else:
                    asset.status = "operational"
                    title = f"Maintenance completed on {asset.name} ({asset.tag_number})"
                events.append(
                    make_event(
                        "maintenance_completed",
                        title,
                        now,
                        zone_id=asset.zone_id,
                        equipment_id=asset.id,
                    )
                )

        events.extend(self._auto_start_spares(spare_groups, now))
        return events, started_maintenance

    def _group_key(self, asset: Equipment, definition: PlantTypeDefinition) -> str | None:
        template = next(
            (
                t
                for zone in definition.zones
                for t in zone.equipment
                if t.tag == asset.tag_number
            ),
            None,
        )
        return template.spare_group if template is not None else None

    def _spare_groups(
        self, equipment: list[Equipment], definition: PlantTypeDefinition
    ) -> dict[str | None, list[Equipment]]:
        groups: dict[str | None, list[Equipment]] = {}
        for asset in equipment:
            key = self._group_key(asset, definition)
            if key is not None:
                groups.setdefault(key, []).append(asset)
        return groups

    def _auto_start_spares(
        self, spare_groups: dict[str | None, list[Equipment]], now: datetime
    ) -> list[Event]:
        events: list[Event] = []
        for members in spare_groups.values():
            if any(m.status == "operational" for m in members):
                continue
            standby = [m for m in members if m.status == "standby"]
            if not standby:
                continue
            spare = standby[0]
            spare.status = "operational"
            events.append(
                make_event(
                    "equipment_started",
                    f"{spare.name} ({spare.tag_number}) auto-started as installed spare",
                    now,
                    description="Duty unit unavailable — standby unit brought online.",
                    zone_id=spare.zone_id,
                    equipment_id=spare.id,
                )
            )
        return events
