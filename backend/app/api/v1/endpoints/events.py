from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_event_service
from app.schemas.common import Page
from app.schemas.event import EventCreate, EventRead, EventType, EventUpdate
from app.services.event import EventService

router = APIRouter(prefix="/events", tags=["events"])

EventServiceDep = Annotated[EventService, Depends(get_event_service)]


@router.get("", response_model=Page[EventRead])
async def list_events(
    service: EventServiceDep,
    zone_id: Annotated[UUID | None, Query()] = None,
    equipment_id: Annotated[UUID | None, Query()] = None,
    permit_id: Annotated[UUID | None, Query()] = None,
    event_type: Annotated[EventType | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> Page[EventRead]:
    items, total = await service.list(
        page=page,
        page_size=page_size,
        zone_id=zone_id,
        equipment_id=equipment_id,
        permit_id=permit_id,
        event_type=event_type,
    )
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.get("/{event_id}", response_model=EventRead)
async def get_event(event_id: UUID, service: EventServiceDep) -> EventRead:
    return await service.get(event_id)


@router.post("", response_model=EventRead, status_code=status.HTTP_201_CREATED)
async def create_event(payload: EventCreate, service: EventServiceDep) -> EventRead:
    return await service.create(payload)


@router.patch("/{event_id}", response_model=EventRead)
async def update_event(event_id: UUID, payload: EventUpdate, service: EventServiceDep) -> EventRead:
    return await service.update(event_id, payload)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(event_id: UUID, service: EventServiceDep) -> None:
    await service.delete(event_id)
