from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_worker_service
from app.schemas.common import Page
from app.schemas.worker import WorkerCreate, WorkerRead, WorkerRole, WorkerUpdate
from app.services.worker import WorkerService

router = APIRouter(prefix="/workers", tags=["workers"])

WorkerServiceDep = Annotated[WorkerService, Depends(get_worker_service)]


@router.get("", response_model=Page[WorkerRead])
async def list_workers(
    service: WorkerServiceDep,
    primary_zone_id: Annotated[UUID | None, Query()] = None,
    role: Annotated[WorkerRole | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> Page[WorkerRead]:
    items, total = await service.list(
        page=page, page_size=page_size, primary_zone_id=primary_zone_id, role=role
    )
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.get("/{worker_id}", response_model=WorkerRead)
async def get_worker(worker_id: UUID, service: WorkerServiceDep) -> WorkerRead:
    return await service.get(worker_id)


@router.post("", response_model=WorkerRead, status_code=status.HTTP_201_CREATED)
async def create_worker(payload: WorkerCreate, service: WorkerServiceDep) -> WorkerRead:
    return await service.create(payload)


@router.patch("/{worker_id}", response_model=WorkerRead)
async def update_worker(
    worker_id: UUID, payload: WorkerUpdate, service: WorkerServiceDep
) -> WorkerRead:
    return await service.update(worker_id, payload)


@router.delete("/{worker_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_worker(worker_id: UUID, service: WorkerServiceDep) -> None:
    await service.delete(worker_id)
