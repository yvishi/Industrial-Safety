"""
The simulation engine: a tick loop that evolves plant state and persists it to Postgres.

Isolation contract: this package never imports from app.api — it talks straight to the
models through its own session, and the API remains a pure read/write window over the DB.
Each tick is one transaction, so a state change and the event describing it can never
disagree.
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.models import Equipment, Event, Permit, Sensor, SensorReading, Worker, Zone
from app.simulation.behaviors.equipment import EquipmentBehavior
from app.simulation.behaviors.permits import PermitBehavior
from app.simulation.behaviors.sensors import SensorBehavior
from app.simulation.behaviors.workers import WorkerBehavior

logger = logging.getLogger(__name__)

PRUNE_EVERY_TICKS = 120  # at 5s ticks: prune old readings every ~10 minutes


class SimulationEngine:
    def __init__(
        self,
        session_factory: async_sessionmaker,
        *,
        tick_seconds: float = 5.0,
        retention_hours: int = 24,
        rng: random.Random | None = None,
    ) -> None:
        self.session_factory = session_factory
        self.tick_seconds = tick_seconds
        self.retention_hours = retention_hours
        rng = rng or random.Random()
        self.sensors = SensorBehavior(rng)
        self.workers = WorkerBehavior(rng)
        self.equipment = EquipmentBehavior(rng)
        self.permits = PermitBehavior(rng)
        self._tick_count = 0

    async def run(self) -> None:
        logger.info("Simulation engine started (tick every %.1fs)", self.tick_seconds)
        while True:
            try:
                await self.tick()
            except asyncio.CancelledError:
                logger.info("Simulation engine stopped")
                raise
            except Exception:
                # A bad tick must not kill the plant; log and try again next tick.
                logger.exception("Simulation tick failed")
            await asyncio.sleep(self.tick_seconds)

    async def tick(self) -> None:
        now = datetime.now(timezone.utc)
        async with self.session_factory() as session:
            zones = (await session.execute(select(Zone))).scalars().all()
            zones_by_id = {z.id: z for z in zones}
            workers = (await session.execute(select(Worker))).scalars().all()
            equipment = (await session.execute(select(Equipment))).scalars().all()
            sensors = (await session.execute(select(Sensor))).scalars().all()
            # All permits (not just open ones) so new-permit numbering never collides.
            permits = (await session.execute(select(Permit))).scalars().all()

            events: list[Event] = []

            readings, sensor_events = self.sensors.tick(list(sensors), zones_by_id, now)
            events.extend(sensor_events)
            session.add_all(readings)

            events.extend(self.workers.tick(list(workers), zones_by_id, now))
            events.extend(self.equipment.tick(list(equipment), zones_by_id, now))

            new_permits, permit_events = self.permits.tick(
                list(permits), list(workers), list(equipment), zones_by_id, now
            )
            events.extend(permit_events)
            session.add_all(new_permits)

            session.add_all(events)

            self._tick_count += 1
            if self._tick_count % PRUNE_EVERY_TICKS == 1:
                cutoff = now - timedelta(hours=self.retention_hours)
                await session.execute(
                    delete(SensorReading).where(SensorReading.recorded_at < cutoff)
                )

            await session.commit()

        if events:
            logger.info("Tick %d: %d event(s)", self._tick_count, len(events))
