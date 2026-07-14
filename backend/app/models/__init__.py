"""Import every model here so Alembic autogenerate and SQLAlchemy's mapper registry see them all."""

from app.database.base import Base
from app.models.equipment import Equipment
from app.models.event import Event
from app.models.permit import Permit
from app.models.plant import Plant
from app.models.risk_snapshot import RiskSnapshot
from app.models.sensor import Sensor, SensorReading
from app.models.worker import Worker
from app.models.zone import Zone

__all__ = [
    "Base",
    "Equipment",
    "Event",
    "Permit",
    "Plant",
    "RiskSnapshot",
    "Sensor",
    "SensorReading",
    "Worker",
    "Zone",
]
