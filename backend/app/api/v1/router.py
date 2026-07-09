from fastapi import APIRouter

from app.api.v1.endpoints import equipment, events, permits, plants, sensors, workers, zones

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(plants.router)
api_router.include_router(zones.router)
api_router.include_router(workers.router)
api_router.include_router(equipment.router)
api_router.include_router(sensors.router)
api_router.include_router(permits.router)
api_router.include_router(events.router)
