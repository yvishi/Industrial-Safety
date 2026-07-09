from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID as UUIDType

from sqlalchemy import Date, ForeignKey, String
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

    zone: Mapped["Zone"] = relationship(back_populates="sensors")
    equipment: Mapped["Equipment | None"] = relationship(back_populates="sensors")
