from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select

from app.models.risk_snapshot import RiskSnapshot
from app.repositories.base import BaseRepository


class RiskRepository(BaseRepository[RiskSnapshot]):
    model = RiskSnapshot
    default_order_by = (RiskSnapshot.evaluated_at.desc(),)

    async def latest_for_zone(self, zone_id: UUID) -> RiskSnapshot | None:
        stmt = (
            select(RiskSnapshot)
            .where(RiskSnapshot.zone_id == zone_id)
            .order_by(RiskSnapshot.evaluated_at.desc())
            .limit(1)
        )
        return (await self.session.execute(stmt)).scalars().first()

    async def history_for_zone(
        self,
        zone_id: UUID,
        *,
        since: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[RiskSnapshot], int]:
        stmt = select(RiskSnapshot).where(RiskSnapshot.zone_id == zone_id)
        if since is not None:
            stmt = stmt.where(RiskSnapshot.evaluated_at >= since)

        total = (await self.session.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()

        stmt = stmt.order_by(RiskSnapshot.evaluated_at.desc()).offset((page - 1) * page_size).limit(page_size)
        items = (await self.session.execute(stmt)).scalars().all()
        return list(items), total

    async def recent_changes(self, *, limit: int = 50) -> list[RiskSnapshot]:
        stmt = select(RiskSnapshot).order_by(RiskSnapshot.evaluated_at.desc()).limit(limit)
        return list((await self.session.execute(stmt)).scalars().all())

    async def previous_before(self, zone_id: UUID, evaluated_at: datetime) -> RiskSnapshot | None:
        """The snapshot immediately preceding a given row, for computing trend at read time."""
        stmt = (
            select(RiskSnapshot)
            .where(RiskSnapshot.zone_id == zone_id, RiskSnapshot.evaluated_at < evaluated_at)
            .order_by(RiskSnapshot.evaluated_at.desc())
            .limit(1)
        )
        return (await self.session.execute(stmt)).scalars().first()
