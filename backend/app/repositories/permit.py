from app.models.permit import Permit
from app.repositories.base import BaseRepository


class PermitRepository(BaseRepository[Permit]):
    model = Permit
