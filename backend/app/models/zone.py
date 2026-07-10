from typing import TYPE_CHECKING
from uuid import UUID as UUIDType

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.equipment import Equipment
    from app.models.event import Event
    from app.models.permit import Permit
    from app.models.plant import Plant
    from app.models.sensor import Sensor
    from app.models.worker import Worker


class Zone(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A physical area of a plant (e.g. a processing unit, tank farm, control room).

    zone_type is intentionally a plain string, not a DB-level enum/constraint — the vocabulary of
    zone types is expected to grow as the product grows, and Postgres enum/CHECK constraints are
    expensive to extend. Validation happens once, at the API boundary (see schemas.zone.ZoneType).
    """

    __tablename__ = "zones"

    plant_id: Mapped[UUIDType] = mapped_column(ForeignKey("plants.id"), index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    zone_type: Mapped[str] = mapped_column(String(40), index=True)
    # Coarse cross-industry grouping (process / storage / safety_systems / ...); the
    # industry-specific identity (crude_distillation, tank_farm, ...) stays in zone_type.
    zone_category: Mapped[str] = mapped_column(String(40), default="process", index=True)
    description: Mapped[str | None] = mapped_column(String(1000))

    # Approximate physical adjacency on site — mirrors the frontend's ZoneGrid layout.
    grid_row: Mapped[int | None] = mapped_column(Integer)
    grid_col: Mapped[int | None] = mapped_column(Integer)

    plant: Mapped["Plant"] = relationship(back_populates="zones")
    workers: Mapped[list["Worker"]] = relationship(
        back_populates="primary_zone", foreign_keys="Worker.primary_zone_id"
    )
    equipment: Mapped[list["Equipment"]] = relationship(
        back_populates="zone", cascade="all, delete-orphan"
    )
    sensors: Mapped[list["Sensor"]] = relationship(back_populates="zone", cascade="all, delete-orphan")
    permits: Mapped[list["Permit"]] = relationship(back_populates="zone", cascade="all, delete-orphan")
    events: Mapped[list["Event"]] = relationship(back_populates="zone")
