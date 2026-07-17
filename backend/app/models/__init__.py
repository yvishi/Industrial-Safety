"""Import every model here so Alembic autogenerate and SQLAlchemy's mapper registry see them all."""

from app.database.base import Base
from app.models.equipment import Equipment
from app.models.event import Event
from app.models.incident import Incident
from app.models.permit import Permit
from app.models.plant import Plant
from app.models.recommendation import Recommendation
from app.models.risk_snapshot import RiskSnapshot
from app.models.sensor import Sensor, SensorReading
from app.models.worker import Worker
from app.models.zone import Zone

__all__ = [
    "Base",
    "Equipment",
    "Event",
    "Incident",
    "Permit",
    "Plant",
    "Recommendation",
    "RiskSnapshot",
    "Sensor",
    "SensorReading",
    "Worker",
    "Zone",
]
