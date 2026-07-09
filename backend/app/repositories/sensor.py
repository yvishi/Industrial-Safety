from app.models.sensor import Sensor
from app.repositories.base import BaseRepository


class SensorRepository(BaseRepository[Sensor]):
    model = Sensor
