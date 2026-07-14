from uuid import UUID

from sqlalchemy import select

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
