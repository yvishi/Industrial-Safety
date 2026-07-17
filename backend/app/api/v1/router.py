from fastapi import APIRouter

from app.api.v1.endpoints import (
    ai,
    equipment,
    events,
    incidents,
    permits,
    plants,
    recommendations,
    reports,
    risk,
    sensors,
    state,
    workers,
    zones,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(state.router)
api_router.include_router(plants.router)
api_router.include_router(zones.router)
api_router.include_router(workers.router)
api_router.include_router(equipment.router)
api_router.include_router(sensors.router)
api_router.include_router(permits.router)
api_router.include_router(events.router)
api_router.include_router(risk.router)
api_router.include_router(recommendations.router)
api_router.include_router(incidents.router)
api_router.include_router(reports.router)
api_router.include_router(ai.router)
