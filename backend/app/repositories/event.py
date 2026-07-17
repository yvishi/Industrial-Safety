from typing import Any
from uuid import UUID

from sqlalchemy import select, update

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

    async def link_by_recommendation_ids(self, recommendation_ids: list[UUID], incident_id: UUID) -> None:
        """Backfills incident_id onto events tied to recommendations that have just been linked
        to an Incident (see IncidentService._link_recommendations). Needed because
        `recommendation_created` fires from RecommendationService.reconcile(), one full service
        earlier in the same tick than the Correlation Engine that decides which Incident (if
        any) that recommendation belongs to — the event genuinely can't know its incident_id at
        the moment it's created."""
        if not recommendation_ids:
            return
        await self.session.execute(
            update(Event)
            .where(Event.recommendation_id.in_(recommendation_ids), Event.incident_id.is_(None))
            .values(incident_id=incident_id)
        )
        await self.session.commit()

    async def link_recent_unlinked(self, zone_id: UUID, event_types: list[str], incident_id: UUID, limit: int = 1) -> None:
        """Backfills incident_id onto the most recent still-unlinked event(s) of the given
        type(s) for a zone — used once, at the moment an Incident opens, to retroactively
        attach the specific risk-level-change event that triggered it (that event has no
        recommendation_id to join through, unlike recommendation-sourced events)."""
        stmt = (
            select(Event)
            .where(Event.zone_id == zone_id, Event.event_type.in_(event_types), Event.incident_id.is_(None))
            .order_by(Event.occurred_at.desc())
            .limit(limit)
        )
        rows = (await self.session.execute(stmt)).scalars().all()
        if not rows:
            return
        await self.session.execute(
            update(Event).where(Event.id.in_([row.id for row in rows])).values(incident_id=incident_id)
        )
        await self.session.commit()
