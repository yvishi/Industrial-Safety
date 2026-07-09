from app.models.event import Event
from app.repositories.event import EventRepository
from app.services.base import BaseService


class EventService(BaseService[Event]):
    entity_name = "Event"

    def __init__(self, repository: EventRepository) -> None:
        super().__init__(repository)
