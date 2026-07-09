from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID as UUIDType

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.equipment import Equipment
    from app.models.permit import Permit
    from app.models.worker import Worker
    from app.models.zone import Zone


class Event(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A plain activity log entry (permit issued, equipment status changed, worker checked in, ...).
    This is deliberately generic and un-opinionated: the future Incident Timeline module is a
    filtered/sorted view over this table, not a separate one. No severity/risk scoring lives here.
    """

    __tablename__ = "events"

    zone_id: Mapped[UUIDType | None] = mapped_column(ForeignKey("zones.id"), index=True, nullable=True)
    equipment_id: Mapped[UUIDType | None] = mapped_column(
        ForeignKey("equipment.id"), index=True, nullable=True
    )
    permit_id: Mapped[UUIDType | None] = mapped_column(ForeignKey("permits.id"), index=True, nullable=True)
    recorded_by_id: Mapped[UUIDType | None] = mapped_column(
        ForeignKey("workers.id"), index=True, nullable=True
    )

    event_type: Mapped[str] = mapped_column(String(50), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String(2000))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    zone: Mapped["Zone | None"] = relationship(back_populates="events")
    equipment: Mapped["Equipment | None"] = relationship(back_populates="events")
    permit: Mapped["Permit | None"] = relationship(back_populates="events")
    recorded_by: Mapped["Worker | None"] = relationship(back_populates="recorded_events")
