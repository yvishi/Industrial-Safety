from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_plant_service
from app.schemas.common import Page
from app.schemas.plant import PlantCreate, PlantRead, PlantUpdate
from app.services.plant import PlantService

router = APIRouter(prefix="/plants", tags=["plants"])

PlantServiceDep = Annotated[PlantService, Depends(get_plant_service)]


@router.get("", response_model=Page[PlantRead])
async def list_plants(
    service: PlantServiceDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> Page[PlantRead]:
    items, total = await service.list(page=page, page_size=page_size)
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.get("/{plant_id}", response_model=PlantRead)
async def get_plant(plant_id: UUID, service: PlantServiceDep) -> PlantRead:
    return await service.get(plant_id)


@router.post("", response_model=PlantRead, status_code=status.HTTP_201_CREATED)
async def create_plant(payload: PlantCreate, service: PlantServiceDep) -> PlantRead:
    return await service.create(payload)


@router.patch("/{plant_id}", response_model=PlantRead)
async def update_plant(plant_id: UUID, payload: PlantUpdate, service: PlantServiceDep) -> PlantRead:
    return await service.update(plant_id, payload)


@router.delete("/{plant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plant(plant_id: UUID, service: PlantServiceDep) -> None:
    await service.delete(plant_id)
