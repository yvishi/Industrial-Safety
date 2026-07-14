from datetime import datetime, timezone
from uuid import UUID

from app.models.zone import Zone
from app.repositories.event import EventRepository
from app.repositories.zone import ZoneRepository
from app.schemas.event import EventType
from app.schemas.zone import ZoneUpdate
from app.services.base import BaseService


class ZoneService(BaseService[Zone]):
    entity_name = "Zone"
    unique_fields = ("code",)

    def __init__(self, repository: ZoneRepository, event_repository: EventRepository) -> None:
        super().__init__(repository)
        self.event_repository = event_repository

    async def update(self, entity_id: UUID, payload: ZoneUpdate) -> Zone:
        previous = await self.get(entity_id)
        previous_esd = previous.emergency_shutdown_active

        updated = await super().update(entity_id, payload)

        values = payload.model_dump(exclude_unset=True)
        if "emergency_shutdown_active" in values and values["emergency_shutdown_active"] != previous_esd:
            activated = values["emergency_shutdown_active"]
            event_type = (
                EventType.EMERGENCY_SHUTDOWN_ACTIVATED if activated else EventType.EMERGENCY_SHUTDOWN_CLEARED
            )
            await self.event_repository.create(
                {
                    "zone_id": updated.id,
                    "event_type": event_type.value,
                    "title": f"Emergency shutdown {'activated' if activated else 'cleared'} in {updated.name}",
                    "description": None,
                    "occurred_at": datetime.now(timezone.utc),
                }
            )

        return updated
