from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_incident_service
from app.schemas.common import Page
from app.schemas.incident import (
    IncidentCloseRequest,
    IncidentEscalateRequest,
    IncidentManualCreate,
    IncidentNoteCreate,
    IncidentRead,
)
from app.services.incident import IncidentService

router = APIRouter(prefix="/incidents", tags=["incidents"])

IncidentServiceDep = Annotated[IncidentService, Depends(get_incident_service)]


@router.get("", response_model=Page[IncidentRead])
async def list_incidents(
    service: IncidentServiceDep,
    zone_id: Annotated[UUID | None, Query()] = None,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    classification: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> Page[IncidentRead]:
    items, total = await service.list_incidents(
        zone_id=zone_id,
        status=status_filter,
        classification=classification,
        page=page,
        page_size=page_size,
    )
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.get("/{incident_id}", response_model=IncidentRead)
async def get_incident(incident_id: UUID, service: IncidentServiceDep) -> IncidentRead:
    return await service.get(incident_id)


@router.post("", response_model=IncidentRead, status_code=status.HTTP_201_CREATED)
async def create_incident(payload: IncidentManualCreate, service: IncidentServiceDep) -> IncidentRead:
    """Manual declare — the path for incidents the sensors never saw at all (e.g. a
    slip-and-fall). System-detected incidents are never created through this endpoint; they're
    opened internally by the Correlation Engine (see RiskScheduler)."""
    return await service.create_manual(payload)


@router.post("/{incident_id}/notes", response_model=IncidentRead)
async def add_incident_note(
    incident_id: UUID, payload: IncidentNoteCreate, service: IncidentServiceDep
) -> IncidentRead:
    return await service.add_note(incident_id, payload)


@router.post("/{incident_id}/escalate", response_model=IncidentRead)
async def escalate_incident(
    incident_id: UUID, payload: IncidentEscalateRequest, service: IncidentServiceDep
) -> IncidentRead:
    return await service.escalate(incident_id, payload)


@router.post("/{incident_id}/close", response_model=IncidentRead)
async def close_incident(
    incident_id: UUID, payload: IncidentCloseRequest, service: IncidentServiceDep
) -> IncidentRead:
    return await service.close(incident_id, payload)
