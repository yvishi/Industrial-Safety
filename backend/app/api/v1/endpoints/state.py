from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import DbSession
from app.schemas.state import PlantState
from app.services.state import StateService

router = APIRouter(prefix="/state", tags=["state"])


def get_state_service(session: DbSession) -> StateService:
    return StateService(session)


StateServiceDep = Annotated[StateService, Depends(get_state_service)]


@router.get("", response_model=PlantState)
async def get_plant_state(service: StateServiceDep) -> PlantState:
    """Aggregate live snapshot of the plant: zones, occupants, equipment, sensors, permits, events."""
    return await service.get_plant_state()
