from app.models.equipment import Equipment
from app.repositories.equipment import EquipmentRepository
from app.services.base import BaseService


class EquipmentService(BaseService[Equipment]):
    entity_name = "Equipment"
    unique_fields = ("tag_number",)

    def __init__(self, repository: EquipmentRepository) -> None:
        super().__init__(repository)
