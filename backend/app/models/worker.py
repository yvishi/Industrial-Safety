from typing import TYPE_CHECKING
from uuid import UUID as UUIDType

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.permit import Permit
    from app.models.zone import Zone


class Worker(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "workers"

    employee_id: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(60), index=True)
    employment_status: Mapped[str] = mapped_column(String(30), default="active")
    shift: Mapped[str | None] = mapped_column(String(20))

    primary_zone_id: Mapped[UUIDType | None] = mapped_column(
        ForeignKey("zones.id"), index=True, nullable=True
    )

    primary_zone: Mapped["Zone | None"] = relationship(back_populates="workers")

    requested_permits: Mapped[list["Permit"]] = relationship(
        back_populates="requested_by", foreign_keys="Permit.requested_by_id"
    )
    approved_permits: Mapped[list["Permit"]] = relationship(
        back_populates="approved_by", foreign_keys="Permit.approved_by_id"
    )
    recorded_events: Mapped[list["Event"]] = relationship(back_populates="recorded_by")
