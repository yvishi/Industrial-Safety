from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID as UUIDType

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.equipment import Equipment
    from app.models.event import Event
    from app.models.worker import Worker
    from app.models.zone import Zone


class Permit(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A Permit-to-Work record — the control mechanism that authorizes hazardous work on site."""

    __tablename__ = "permits"

    zone_id: Mapped[UUIDType] = mapped_column(ForeignKey("zones.id"), index=True)
    equipment_id: Mapped[UUIDType | None] = mapped_column(
        ForeignKey("equipment.id"), index=True, nullable=True
    )
    permit_number: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    permit_type: Mapped[str] = mapped_column(String(40), index=True)
    # Isolation standard demanded before the work may start (lockout_tagout, blind_purge_and_gas_test, ...).
    required_isolation: Mapped[str | None] = mapped_column(String(40))
    description: Mapped[str | None] = mapped_column(String(1000))
    status: Mapped[str] = mapped_column(String(30), default="draft", index=True)

    requested_by_id: Mapped[UUIDType] = mapped_column(ForeignKey("workers.id"), index=True)
    approved_by_id: Mapped[UUIDType | None] = mapped_column(
        ForeignKey("workers.id"), index=True, nullable=True
    )

    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    zone: Mapped["Zone"] = relationship(back_populates="permits")
    equipment: Mapped["Equipment | None"] = relationship(back_populates="permits")
    requested_by: Mapped["Worker"] = relationship(
        back_populates="requested_permits", foreign_keys=[requested_by_id]
    )
    approved_by: Mapped["Worker | None"] = relationship(
        back_populates="approved_permits", foreign_keys=[approved_by_id]
    )
    events: Mapped[list["Event"]] = relationship(back_populates="permit")
