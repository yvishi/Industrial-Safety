from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_equipment_service
from app.schemas.common import Page
from app.schemas.equipment import EquipmentCreate, EquipmentRead, EquipmentType, EquipmentUpdate
from app.services.equipment import EquipmentService

router = APIRouter(prefix="/equipment", tags=["equipment"])

EquipmentServiceDep = Annotated[EquipmentService, Depends(get_equipment_service)]


@router.get("", response_model=Page[EquipmentRead])
async def list_equipment(
    service: EquipmentServiceDep,
    zone_id: Annotated[UUID | None, Query()] = None,
    equipment_type: Annotated[EquipmentType | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> Page[EquipmentRead]:
    items, total = await service.list(
        page=page, page_size=page_size, zone_id=zone_id, equipment_type=equipment_type
    )
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.get("/{equipment_id}", response_model=EquipmentRead)
async def get_equipment(equipment_id: UUID, service: EquipmentServiceDep) -> EquipmentRead:
    return await service.get(equipment_id)


@router.post("", response_model=EquipmentRead, status_code=status.HTTP_201_CREATED)
async def create_equipment(payload: EquipmentCreate, service: EquipmentServiceDep) -> EquipmentRead:
    return await service.create(payload)


@router.patch("/{equipment_id}", response_model=EquipmentRead)
async def update_equipment(
    equipment_id: UUID, payload: EquipmentUpdate, service: EquipmentServiceDep
) -> EquipmentRead:
    return await service.update(equipment_id, payload)


@router.delete("/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_equipment(equipment_id: UUID, service: EquipmentServiceDep) -> None:
    await service.delete(equipment_id)
