from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.models.sensor import Sensor, SensorReading
from app.repositories.sensor import SensorRepository
from app.services.base import BaseService


class SensorService(BaseService[Sensor]):
    entity_name = "Sensor"
    unique_fields = ("tag_number",)

    def __init__(self, repository: SensorRepository) -> None:
        super().__init__(repository)
        self._sensor_repository = repository

    async def get_readings(self, sensor_id: UUID, *, minutes: int) -> list[SensorReading]:
        await self.get(sensor_id)  # 404 if the sensor doesn't exist
        since = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        return await self._sensor_repository.list_readings(sensor_id, since)
