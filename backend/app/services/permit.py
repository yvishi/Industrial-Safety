from app.models.permit import Permit
from app.repositories.permit import PermitRepository
from app.services.base import BaseService


class PermitService(BaseService[Permit]):
    entity_name = "Permit"
    unique_fields = ("permit_number",)

    def __init__(self, repository: PermitRepository) -> None:
        super().__init__(repository)
