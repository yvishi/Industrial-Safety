from app.models.plant import Plant
from app.repositories.base import BaseRepository


class PlantRepository(BaseRepository[Plant]):
    model = Plant
