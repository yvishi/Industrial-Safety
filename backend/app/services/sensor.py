from app.models.sensor import Sensor
from app.repositories.sensor import SensorRepository
from app.services.base import BaseService


class SensorService(BaseService[Sensor]):
    entity_name = "Sensor"
    unique_fields = ("tag_number",)

    def __init__(self, repository: SensorRepository) -> None:
        super().__init__(repository)
