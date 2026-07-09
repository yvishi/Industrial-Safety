from app.models.worker import Worker
from app.repositories.base import BaseRepository


class WorkerRepository(BaseRepository[Worker]):
    model = Worker
