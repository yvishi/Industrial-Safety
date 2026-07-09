from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID as UUIDType

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.permit import Permit
    from app.models.sensor import Sensor
    from app.models.zone import Zone


class Equipment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A physical asset on site, identified by its P&ID tag number (e.g. P-101A, T-201, E-301)."""

    __tablename__ = "equipment"

    zone_id: Mapped[UUIDType] = mapped_column(ForeignKey("zones.id"), index=True)
    tag_number: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    equipment_type: Mapped[str] = mapped_column(String(40), index=True)
    manufacturer: Mapped[str | None] = mapped_column(String(120))
    model_number: Mapped[str | None] = mapped_column(String(120))
    installation_date: Mapped[date | None] = mapped_column(Date)

    # Static asset-management metadata (like a CMMS record) — not a computed/live value.
    status: Mapped[str] = mapped_column(String(30), default="operational")
    criticality: Mapped[str | None] = mapped_column(String(30))

    zone: Mapped["Zone"] = relationship(back_populates="equipment")
    sensors: Mapped[list["Sensor"]] = relationship(back_populates="equipment")
    permits: Mapped[list["Permit"]] = relationship(back_populates="equipment")
    events: Mapped[list["Event"]] = relationship(back_populates="equipment")
