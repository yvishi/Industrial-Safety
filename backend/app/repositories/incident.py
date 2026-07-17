from uuid import UUID

from sqlalchemy import select

from app.models.incident import Incident
from app.repositories.base import BaseRepository

_OPEN = "open"


class IncidentRepository(BaseRepository[Incident]):
    model = Incident
    default_order_by = (Incident.opened_at.desc(),)

    async def open_for_zone(self, zone_id: UUID) -> Incident | None:
        stmt = select(Incident).where(Incident.primary_zone_id == zone_id, Incident.status == _OPEN)
        return (await self.session.execute(stmt)).scalars().first()

    async def all_for_zone(self, zone_id: UUID) -> list[Incident]:
        stmt = (
            select(Incident).where(Incident.primary_zone_id == zone_id).order_by(Incident.opened_at.desc())
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def all_open(self) -> list[Incident]:
        stmt = select(Incident).where(Incident.status == _OPEN).order_by(Incident.opened_at.desc())
        return list((await self.session.execute(stmt)).scalars().all())
