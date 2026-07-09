from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_zone_service
from app.schemas.common import Page
from app.schemas.zone import ZoneCreate, ZoneRead, ZoneType, ZoneUpdate
from app.services.zone import ZoneService

router = APIRouter(prefix="/zones", tags=["zones"])

ZoneServiceDep = Annotated[ZoneService, Depends(get_zone_service)]


@router.get("", response_model=Page[ZoneRead])
async def list_zones(
    service: ZoneServiceDep,
    plant_id: Annotated[UUID | None, Query()] = None,
    zone_type: Annotated[ZoneType | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> Page[ZoneRead]:
    items, total = await service.list(
        page=page, page_size=page_size, plant_id=plant_id, zone_type=zone_type
    )
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.get("/{zone_id}", response_model=ZoneRead)
async def get_zone(zone_id: UUID, service: ZoneServiceDep) -> ZoneRead:
    return await service.get(zone_id)


@router.post("", response_model=ZoneRead, status_code=status.HTTP_201_CREATED)
async def create_zone(payload: ZoneCreate, service: ZoneServiceDep) -> ZoneRead:
    return await service.create(payload)


@router.patch("/{zone_id}", response_model=ZoneRead)
async def update_zone(zone_id: UUID, payload: ZoneUpdate, service: ZoneServiceDep) -> ZoneRead:
    return await service.update(zone_id, payload)


@router.delete("/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_zone(zone_id: UUID, service: ZoneServiceDep) -> None:
    await service.delete(zone_id)
