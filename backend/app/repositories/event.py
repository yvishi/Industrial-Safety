from typing import Any

from app.models.event import Event
from app.repositories.base import BaseRepository
from app.schemas.event import EVENT_SEVERITY_MAP, EventSeverity


class EventRepository(BaseRepository[Event]):
    model = Event
    # "Recent events" must actually mean recent — newest first everywhere.
    default_order_by = (Event.occurred_at.desc(),)

    async def create(self, values: dict[str, Any]) -> Event:
        """Severity is always derived from event_type server-side, never accepted from a
        caller — see EVENT_SEVERITY_MAP. Centralizing it here means none of the existing
        internal emit call sites (equipment/permit/worker/zone/recommendation services) need
        to change to start carrying a severity."""
        severity = EVENT_SEVERITY_MAP.get(values["event_type"], EventSeverity.INFO).value
        return await super().create({**values, "severity": severity})
