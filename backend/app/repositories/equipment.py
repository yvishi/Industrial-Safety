from app.models.equipment import Equipment
from app.repositories.base import BaseRepository


class EquipmentRepository(BaseRepository[Equipment]):
    model = Equipment
