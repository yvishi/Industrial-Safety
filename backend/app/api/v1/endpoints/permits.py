from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_permit_service
from app.schemas.common import Page
from app.schemas.permit import PermitCreate, PermitRead, PermitStatus, PermitType, PermitUpdate
from app.services.permit import PermitService

router = APIRouter(prefix="/permits", tags=["permits"])

PermitServiceDep = Annotated[PermitService, Depends(get_permit_service)]


@router.get("", response_model=Page[PermitRead])
async def list_permits(
    service: PermitServiceDep,
    zone_id: Annotated[UUID | None, Query()] = None,
    equipment_id: Annotated[UUID | None, Query()] = None,
    permit_type: Annotated[PermitType | None, Query()] = None,
    status_: Annotated[PermitStatus | None, Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> Page[PermitRead]:
    items, total = await service.list(
        page=page,
        page_size=page_size,
        zone_id=zone_id,
        equipment_id=equipment_id,
        permit_type=permit_type,
        status=status_,
    )
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.get("/{permit_id}", response_model=PermitRead)
async def get_permit(permit_id: UUID, service: PermitServiceDep) -> PermitRead:
    return await service.get(permit_id)


@router.post("", response_model=PermitRead, status_code=status.HTTP_201_CREATED)
async def create_permit(payload: PermitCreate, service: PermitServiceDep) -> PermitRead:
    return await service.create(payload)


@router.patch("/{permit_id}", response_model=PermitRead)
async def update_permit(
    permit_id: UUID, payload: PermitUpdate, service: PermitServiceDep
) -> PermitRead:
    return await service.update(permit_id, payload)


@router.delete("/{permit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_permit(permit_id: UUID, service: PermitServiceDep) -> None:
    await service.delete(permit_id)
