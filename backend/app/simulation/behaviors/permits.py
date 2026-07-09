"""
Permit-to-Work lifecycle behavior.

Existing permits walk the chain draft -> pending_approval -> approved -> active -> closed/expired
by simple time- and probability-based rules; occasionally a new realistic permit is drafted so
the permit board stays alive during long demos. Approvals are assigned to actual safety
officers / shift supervisors from the worker roster.
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
from app.simulation.events import make_event

P_SUBMIT = 0.010  # draft -> pending_approval
P_APPROVE = 0.008  # pending_approval -> approved
P_CLOSE_EARLY = 0.0010  # active -> closed before expiry (work finished)
P_NEW_PERMIT = 0.0050  # a new draft appears (~1 per half hour at 5s ticks)

APPROVER_ROLES = {"safety_officer", "shift_supervisor"}
REQUESTER_ROLES = {"process_operator", "maintenance_technician", "contractor"}

PERMIT_TEMPLATES: list[tuple[str, str]] = [
    ("hot_work", "Weld repair on {target}"),
    ("hot_work", "Grinding and cutting near {target}"),
    ("lockout_tagout", "Isolation for mechanical work on {target}"),
    ("confined_space", "Internal inspection of {target}"),
    ("working_at_height", "Elevated platform work at {target}"),
    ("electrical", "Motor control inspection on {target}"),
]


class PermitBehavior:
    def __init__(self, rng: random.Random) -> None:
        self.rng = rng

    def tick(
        self,
        permits: list[Permit],
        workers: list[Worker],
        equipment: list[Equipment],
        zones_by_id: dict[UUID, Zone],
        now: datetime,
    ) -> tuple[list[Permit], list[Event]]:
        events: list[Event] = []
        new_permits: list[Permit] = []

        approvers = [w for w in workers if w.role in APPROVER_ROLES and w.employment_status == "active"]
        requesters = [w for w in workers if w.role in REQUESTER_ROLES]

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

        if requesters and self.rng.random() < P_NEW_PERMIT:
            permit = self._draft_new_permit(permits, requesters, equipment, zones_by_id)
            if permit is not None:
                new_permits.append(permit)

        return new_permits, events

    def _draft_new_permit(
        self,
        permits: list[Permit],
        requesters: list[Worker],
        equipment: list[Equipment],
        zones_by_id: dict[UUID, Zone],
    ) -> Permit | None:
        # Permits attach to real work: pick an asset, inherit its zone.
        candidates = [e for e in equipment if e.status != "decommissioned"]
        if not candidates:
            return None
        asset = self.rng.choice(candidates)
        zone = zones_by_id.get(asset.zone_id)
        if zone is None:
            return None

        permit_type, template = self.rng.choice(PERMIT_TEMPLATES)
        requester = self.rng.choice(requesters)

        return Permit(
            permit_number=self._next_permit_number(permits),
            permit_type=permit_type,
            description=template.format(target=f"{asset.name} ({asset.tag_number})"),
            status="draft",
            zone_id=zone.id,
            equipment_id=asset.id,
            requested_by_id=requester.id,
        )

    def _next_permit_number(self, permits: list[Permit]) -> str:
        highest = 0
        for permit in permits:
            match = re.fullmatch(r"PTW-(\d{4})-(\d+)", permit.permit_number)
            if match:
                highest = max(highest, int(match.group(2)))
        return f"PTW-2026-{highest + 1:04d}"
