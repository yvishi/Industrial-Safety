from app.models.zone import Zone
from app.repositories.zone import ZoneRepository
from app.services.base import BaseService


class ZoneService(BaseService[Zone]):
    entity_name = "Zone"
    unique_fields = ("code",)

    def __init__(self, repository: ZoneRepository) -> None:
        super().__init__(repository)
