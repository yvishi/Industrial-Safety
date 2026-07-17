from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.repositories.equipment import EquipmentRepository
from app.repositories.event import EventRepository
from app.repositories.incident import IncidentRepository
from app.repositories.permit import PermitRepository
from app.repositories.plant import PlantRepository
from app.repositories.recommendation import RecommendationRepository
from app.repositories.risk import RiskRepository
from app.repositories.sensor import SensorRepository
from app.repositories.worker import WorkerRepository
from app.repositories.zone import ZoneRepository
from app.risk_engine.facts_builder import ZoneFactsBuilder
from app.services.equipment import EquipmentService
from app.services.event import EventService
from app.services.incident import IncidentService
from app.services.permit import PermitService
from app.services.plant import PlantService
from app.services.recommendation import RecommendationService
from app.services.reporting import ReportingService
from app.services.risk import RiskService
from app.services.sensor import SensorService
from app.services.worker import WorkerService
from app.services.zone import ZoneService

DbSession = Annotated[AsyncSession, Depends(get_db)]


def get_plant_service(session: DbSession) -> PlantService:
    return PlantService(PlantRepository(session))


def get_zone_service(session: DbSession) -> ZoneService:
    return ZoneService(ZoneRepository(session), EventRepository(session))


def get_worker_service(session: DbSession) -> WorkerService:
    return WorkerService(WorkerRepository(session))


def get_equipment_service(session: DbSession) -> EquipmentService:
    return EquipmentService(EquipmentRepository(session))


def get_sensor_service(session: DbSession) -> SensorService:
    return SensorService(SensorRepository(session))


def get_permit_service(session: DbSession) -> PermitService:
    return PermitService(PermitRepository(session))


def get_event_service(session: DbSession) -> EventService:
    return EventService(EventRepository(session))


def get_risk_service(session: DbSession) -> RiskService:
    return RiskService(RiskRepository(session), ZoneFactsBuilder(session), EventRepository(session))


def get_recommendation_service(session: DbSession) -> RecommendationService:
    return RecommendationService(
        RecommendationRepository(session), ZoneRepository(session), EventRepository(session), RiskRepository(session)
    )


def get_incident_service(session: DbSession) -> IncidentService:
    return IncidentService(
        IncidentRepository(session),
        RecommendationRepository(session),
        EventRepository(session),
        ZoneRepository(session),
    )


def get_reporting_service(session: DbSession) -> ReportingService:
    return ReportingService(session)
