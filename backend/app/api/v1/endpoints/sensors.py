from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_sensor_service
from app.schemas.common import Page
from app.schemas.sensor import SensorCreate, SensorRead, SensorType, SensorUpdate
from app.services.sensor import SensorService

router = APIRouter(prefix="/sensors", tags=["sensors"])

SensorServiceDep = Annotated[SensorService, Depends(get_sensor_service)]


@router.get("", response_model=Page[SensorRead])
async def list_sensors(
    service: SensorServiceDep,
    zone_id: Annotated[UUID | None, Query()] = None,
    equipment_id: Annotated[UUID | None, Query()] = None,
    sensor_type: Annotated[SensorType | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> Page[SensorRead]:
    items, total = await service.list(
        page=page,
        page_size=page_size,
        zone_id=zone_id,
        equipment_id=equipment_id,
        sensor_type=sensor_type,
    )
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.get("/{sensor_id}", response_model=SensorRead)
async def get_sensor(sensor_id: UUID, service: SensorServiceDep) -> SensorRead:
    return await service.get(sensor_id)


@router.post("", response_model=SensorRead, status_code=status.HTTP_201_CREATED)
async def create_sensor(payload: SensorCreate, service: SensorServiceDep) -> SensorRead:
    return await service.create(payload)


@router.patch("/{sensor_id}", response_model=SensorRead)
async def update_sensor(
    sensor_id: UUID, payload: SensorUpdate, service: SensorServiceDep
) -> SensorRead:
    return await service.update(sensor_id, payload)


@router.delete("/{sensor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sensor(sensor_id: UUID, service: SensorServiceDep) -> None:
    await service.delete(sensor_id)
