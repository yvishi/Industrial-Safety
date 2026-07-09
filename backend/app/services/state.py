from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models import Equipment, Event, Permit, Plant, Sensor, Worker, Zone
from app.schemas.equipment import EquipmentRead
from app.schemas.event import EventRead
from app.schemas.permit import PermitRead
from app.schemas.plant import PlantRead
from app.schemas.sensor import SensorRead
from app.schemas.state import PlantState, ZoneState
from app.schemas.worker import WorkerRead
from app.schemas.zone import ZoneRead

RECENT_EVENT_LIMIT = 20


class StateService:
    """Builds the aggregate plant snapshot the frontend polls. Read-only."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_plant_state(self) -> PlantState:
        plant = (await self.session.execute(select(Plant).limit(1))).scalars().first()
        if plant is None:
            raise NotFoundError("No plant configured")

        zones = (
            (await self.session.execute(select(Zone).where(Zone.plant_id == plant.id).order_by(Zone.code)))
            .scalars()
            .all()
        )
        workers = (await self.session.execute(select(Worker))).scalars().all()
        equipment = (await self.session.execute(select(Equipment).order_by(Equipment.tag_number))).scalars().all()
        sensors = (await self.session.execute(select(Sensor).order_by(Sensor.tag_number))).scalars().all()
        active_permits = (
            (await self.session.execute(select(Permit).where(Permit.status == "active")))
            .scalars()
            .all()
        )
        recent_events = (
            (
                await self.session.execute(
                    select(Event).order_by(Event.occurred_at.desc()).limit(RECENT_EVENT_LIMIT)
                )
            )
            .scalars()
            .all()
        )

        active_permit_counts: dict = {}
        for permit in active_permits:
            active_permit_counts[permit.zone_id] = active_permit_counts.get(permit.zone_id, 0) + 1

        zone_states = [
            ZoneState(
                zone=ZoneRead.model_validate(zone),
                workers=[
                    WorkerRead.model_validate(w) for w in workers if w.current_zone_id == zone.id
                ],
                equipment=[
                    EquipmentRead.model_validate(e) for e in equipment if e.zone_id == zone.id
                ],
                sensors=[SensorRead.model_validate(s) for s in sensors if s.zone_id == zone.id],
                active_permit_count=active_permit_counts.get(zone.id, 0),
            )
            for zone in zones
        ]

        return PlantState(
            plant=PlantRead.model_validate(plant),
            generated_at=datetime.now(timezone.utc),
            zones=zone_states,
            active_permits=[PermitRead.model_validate(p) for p in active_permits],
            recent_events=[EventRead.model_validate(e) for e in recent_events],
        )
