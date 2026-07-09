from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID as UUIDType

from sqlalchemy import Date, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.equipment import Equipment
    from app.models.zone import Zone


class Sensor(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A registry entry for an installed instrument (e.g. TT-101, PT-201, GD-301) — what exists,
    where, and what it measures. This is a catalog record, not a telemetry/reading store: live
    sensor data is an explicitly separate future module with its own storage shape.
    """

    __tablename__ = "sensors"

    zone_id: Mapped[UUIDType] = mapped_column(ForeignKey("zones.id"), index=True)
    equipment_id: Mapped[UUIDType | None] = mapped_column(
        ForeignKey("equipment.id"), index=True, nullable=True
    )
    tag_number: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    sensor_type: Mapped[str] = mapped_column(String(40), index=True)
    unit_of_measure: Mapped[str] = mapped_column(String(20))
    installation_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(30), default="active")

    # Denormalized latest reading, kept in sync by the simulation engine so the
    # current-state endpoint never needs a latest-per-sensor subquery.
    last_value: Mapped[float | None] = mapped_column(Float)
    last_reading_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    zone: Mapped["Zone"] = relationship(back_populates="sensors")
    equipment: Mapped["Equipment | None"] = relationship(back_populates="sensors")
    readings: Mapped[list["SensorReading"]] = relationship(
        back_populates="sensor", cascade="all, delete-orphan"
    )


class SensorReading(UUIDPrimaryKeyMixin, Base):
    """
    Time-series telemetry, produced by the simulation engine (later: real instrument data).
    Deliberately separate from the Sensor catalog record; pruned to a retention window so
    the dev database stays small.
    """

    __tablename__ = "sensor_readings"

    sensor_id: Mapped[UUIDType] = mapped_column(ForeignKey("sensors.id"), index=True)
    value: Mapped[float] = mapped_column(Float)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    sensor: Mapped["Sensor"] = relationship(back_populates="readings")
