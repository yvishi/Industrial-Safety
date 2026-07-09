from app.models.plant import Plant
from app.repositories.plant import PlantRepository
from app.services.base import BaseService


class PlantService(BaseService[Plant]):
    entity_name = "Plant"
    unique_fields = ("code",)

    def __init__(self, repository: PlantRepository) -> None:
        super().__init__(repository)
