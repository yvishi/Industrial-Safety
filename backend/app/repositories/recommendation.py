from uuid import UUID

from sqlalchemy import select, update

from app.models.recommendation import Recommendation
from app.repositories.base import BaseRepository

_RESOLVED = "resolved"


class RecommendationRepository(BaseRepository[Recommendation]):
    model = Recommendation
    default_order_by = (Recommendation.last_seen_at.desc(),)

    async def active_for_zone(self, zone_id: UUID) -> list[Recommendation]:
        stmt = select(Recommendation).where(
            Recommendation.zone_id == zone_id, Recommendation.state != _RESOLVED
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def link_to_incident(self, recommendation_ids: list[UUID], incident_id: UUID) -> None:
        """Bulk-links recommendations to an Incident in one statement — used by
        IncidentService, which otherwise would issue one UPDATE (+ commit) per row every time
        the Correlation Engine's active set for a zone changes."""
        await self.session.execute(
            update(Recommendation).where(Recommendation.id.in_(recommendation_ids)).values(incident_id=incident_id)
        )
        await self.session.commit()

    async def all_for_zone(self, zone_id: UUID) -> list[Recommendation]:
        stmt = (
            select(Recommendation)
            .where(Recommendation.zone_id == zone_id)
            .order_by(Recommendation.last_seen_at.desc())
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def all_active(self) -> list[Recommendation]:
        stmt = select(Recommendation).where(Recommendation.state != _RESOLVED)
        return list((await self.session.execute(stmt)).scalars().all())
