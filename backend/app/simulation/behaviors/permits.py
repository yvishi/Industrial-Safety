"""
Permit-to-Work lifecycle behavior — plant-type-driven.

Existing permits walk the chain draft -> pending_approval -> approved -> active ->
closed/expired by simple time- and probability-based rules; approvals are assigned to real
approvers from the worker roster (roles from the plant type's tuning).

New permits arise two ways, both from the plant type's permit catalog:
- when an asset enters maintenance, the authorizing permit is drafted against it (permit
  activity follows the maintenance schedule, as on a real site);
- occasionally a planned-work permit appears on its own so the board stays alive.
The permit type is chosen from the catalog's applies_to mapping (LOTO for a pump, confined
space for a tank, ...) and carries that type's required isolation standard.
"""

import random
import re
from datetime import datetime, timedelta
from uuid import UUID

from app.models.equipment import Equipment
from app.models.event import Event
from app.models.permit import Permit
from app.models.worker import Worker
from app.models.zone import Zone
from app.plant_types.schema import PlantTypeDefinition
from app.simulation.events import make_event

P_SUBMIT = 0.010  # draft -> pending_approval
P_APPROVE = 0.008  # pending_approval -> approved
P_CLOSE_EARLY = 0.0010  # active -> closed before expiry (work finished)

_PERMIT_NUMBER_RE = re.compile(r"PTW-(\d{4})-(\d+)")


class PermitBehavior:
    def __init__(self, rng: random.Random) -> None:
        self.rng = rng

    def tick(
        self,
        permits: list[Permit],
        workers: list[Worker],
        equipment: list[Equipment],
        zones_by_id: dict[UUID, Zone],
        definition: PlantTypeDefinition,
        started_maintenance: list[Equipment],
        now: datetime,
    ) -> tuple[list[Permit], list[Event]]:
        events: list[Event] = []
        new_permits: list[Permit] = []
        tuning = definition.tuning

        approvers = [
            w for w in workers if w.role in tuning.approver_roles and w.employment_status == "active"
        ]
        requesters = [w for w in workers if w.role in tuning.requester_roles]

        for permit in permits:
            if permit.status == "draft" and self.rng.random() < P_SUBMIT:
                permit.status = "pending_approval"
                events.append(
                    make_event(
                        "permit_issued",
                        f"Permit {permit.permit_number} submitted for approval",
                        now,
                        zone_id=permit.zone_id,
                        equipment_id=permit.equipment_id,
                        permit_id=permit.id,
                        recorded_by_id=permit.requested_by_id,
                    )
                )

            elif permit.status == "pending_approval" and approvers and self.rng.random() < P_APPROVE:
                approver = self.rng.choice(approvers)
                permit.status = "approved"
                permit.approved_by_id = approver.id
                permit.valid_from = now
                permit.valid_until = now + timedelta(hours=self.rng.uniform(2, 8))
                events.append(
                    make_event(
                        "permit_approved",
                        f"Permit {permit.permit_number} approved",
                        now,
                        zone_id=permit.zone_id,
                        equipment_id=permit.equipment_id,
                        permit_id=permit.id,
                        recorded_by_id=approver.id,
                    )
                )

            elif permit.status == "approved" and permit.valid_from and now >= permit.valid_from:
                permit.status = "active"
                events.append(
                    make_event(
                        "permit_activated",
                        f"Permit {permit.permit_number} is now active",
                        now,
                        zone_id=permit.zone_id,
                        equipment_id=permit.equipment_id,
                        permit_id=permit.id,
                    )
                )

            elif permit.status == "active":
                if permit.valid_until and now > permit.valid_until:
                    permit.status = "expired"
                    events.append(
                        make_event(
                            "permit_expired",
                            f"Permit {permit.permit_number} expired",
                            now,
                            zone_id=permit.zone_id,
                            equipment_id=permit.equipment_id,
                            permit_id=permit.id,
                        )
                    )
                elif self.rng.random() < P_CLOSE_EARLY:
                    permit.status = "closed"
                    events.append(
                        make_event(
                            "permit_closed",
                            f"Permit {permit.permit_number} closed out",
                            now,
                            zone_id=permit.zone_id,
                            equipment_id=permit.equipment_id,
                            permit_id=permit.id,
                            recorded_by_id=permit.requested_by_id,
                        )
                    )

        if requesters:
            # Work that just started needs its authorization on the board.
            for asset in started_maintenance:
                if self.rng.random() < tuning.p_permit_follows_maintenance:
                    permit = self._draft_permit(asset, permits, new_permits, requesters, definition, now)
                    if permit is not None:
                        new_permits.append(permit)

            # Occasionally, planned work is drafted ahead of any status change.
            if self.rng.random() < tuning.p_new_permit:
                candidates = [e for e in equipment if e.status != "decommissioned"]
                if candidates:
                    asset = self.rng.choice(candidates)
                    permit = self._draft_permit(asset, permits, new_permits, requesters, definition, now)
                    if permit is not None:
                        new_permits.append(permit)

        return new_permits, events

    def _draft_permit(
        self,
        asset: Equipment,
        permits: list[Permit],
        pending_new: list[Permit],
        requesters: list[Worker],
        definition: PlantTypeDefinition,
        now: datetime,
    ) -> Permit | None:
        permit_types = definition.permit_types_for_equipment(asset.equipment_type)
        if not permit_types:
            return None
        permit_type = self.rng.choice(permit_types)
        template = self.rng.choice(permit_type.description_templates)
        requester = self.rng.choice(requesters)

        return Permit(
            permit_number=self._next_permit_number(permits, pending_new, now),
            permit_type=permit_type.slug,
            required_isolation=permit_type.required_isolation,
            description=template.format(target=f"{asset.name} ({asset.tag_number})"),
            status="draft",
            zone_id=asset.zone_id,
            equipment_id=asset.id,
            requested_by_id=requester.id,
        )

    def _next_permit_number(
        self, permits: list[Permit], pending_new: list[Permit], now: datetime
    ) -> str:
        highest = 0
        for permit in [*permits, *pending_new]:
            match = _PERMIT_NUMBER_RE.fullmatch(permit.permit_number)
            if match:
                highest = max(highest, int(match.group(2)))
        return f"PTW-{now.year}-{highest + 1:04d}"
