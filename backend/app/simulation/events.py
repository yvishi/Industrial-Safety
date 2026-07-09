from datetime import datetime
from uuid import UUID

from app.models.event import Event


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
    return Event(
        event_type=event_type,
        title=title,
        description=description,
        occurred_at=occurred_at,
        zone_id=zone_id,
        equipment_id=equipment_id,
        permit_id=permit_id,
        recorded_by_id=recorded_by_id,
    )
