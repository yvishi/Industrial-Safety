from app.models.event import Event
from app.repositories.base import BaseRepository


class EventRepository(BaseRepository[Event]):
    model = Event
    # "Recent events" must actually mean recent — newest first everywhere.
    default_order_by = (Event.occurred_at.desc(),)
