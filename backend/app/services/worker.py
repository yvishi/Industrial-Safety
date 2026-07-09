from app.models.worker import Worker
from app.repositories.worker import WorkerRepository
from app.services.base import BaseService


class WorkerService(BaseService[Worker]):
    entity_name = "Worker"
    unique_fields = ("employee_id",)

    def __init__(self, repository: WorkerRepository) -> None:
        super().__init__(repository)
