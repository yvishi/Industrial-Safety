from typing import TYPE_CHECKING

from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.zone import Zone


class Plant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "plants"

    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    # Selects the PlantTypeDefinition (app/plant_types/) that drives the simulator and seeded
    # vocabulary for this site — the industry the plant belongs to.
    plant_type: Mapped[str] = mapped_column(String(40), default="crude_oil_refinery", index=True)
    description: Mapped[str | None] = mapped_column(String(1000))

    city: Mapped[str | None] = mapped_column(String(120))
    region: Mapped[str | None] = mapped_column(String(120))
    country: Mapped[str | None] = mapped_column(String(120))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    timezone: Mapped[str] = mapped_column(String(60), default="UTC")

    zones: Mapped[list["Zone"]] = relationship(back_populates="plant", cascade="all, delete-orphan")
