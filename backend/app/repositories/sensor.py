from datetime import datetime
from uuid import UUID

from sqlalchemy import select

from app.models.sensor import Sensor, SensorReading
from app.repositories.base import BaseRepository


class SensorRepository(BaseRepository[Sensor]):
    model = Sensor

    async def list_readings(self, sensor_id: UUID, since: datetime) -> list[SensorReading]:
        stmt = (
            select(SensorReading)
            .where(SensorReading.sensor_id == sensor_id, SensorReading.recorded_at >= since)
            .order_by(SensorReading.recorded_at.asc())
        )
        return list((await self.session.execute(stmt)).scalars().all())
