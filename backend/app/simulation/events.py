from datetime import datetime
from uuid import UUID

from app.models.event import Event
from app.schemas.event import EVENT_SEVERITY_MAP, EventSeverity


def make_event(
    event_type: str,
    title: str,
    occurred_at: datetime,
    *,
    description: str | None = None,
    zone_id: UUID | None = None,
    equipment_id: UUID | None = None,
    permit_id: UUID | None = None,
    recorded_by_id: UUID | None = None,
) -> Event:
    # Built directly (not via EventRepository.create()) since the simulator batches many
    # events per tick — severity still has to be derived the same way, so it's computed here
    # rather than left for a repository this call never goes through.
    return Event(
        event_type=event_type,
        severity=EVENT_SEVERITY_MAP.get(event_type, EventSeverity.INFO).value,
        title=title,
        description=description,
        occurred_at=occurred_at,
        zone_id=zone_id,
        equipment_id=equipment_id,
        permit_id=permit_id,
        recorded_by_id=recorded_by_id,
    )
