from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID as UUIDType

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.zone import Zone

# Real JSONB on Postgres; falls back to JSON (TEXT-backed) on SQLite so the in-memory
# test database (app/database/base.py's dual-dialect convention) can still create_all().
_JSONVariant = JSON().with_variant(JSONB(), "postgresql")


class RiskSnapshot(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A frozen Compound Risk Engine assessment for one zone at one point in time.

    Only written when a zone's risk level changes or its score moves by more than the
    configured threshold since the last snapshot (see risk_engine/services/risk.py) — every
    row here is, by construction, a meaningful change, not a periodic sample.

    score/level/categories/contributors/explanation/confidence/engine_version are frozen facts
    as evaluated at the time — never recomputed against newer rule config later, so historical
    snapshots don't silently drift when weights are retuned. Cheap mechanical derivations of
    these frozen fields (triggered_rules, confidence_label, trend vs. the previous row) are
    computed at read time instead of stored, since they carry no risk of drifting.
    """

    __tablename__ = "risk_snapshots"

    zone_id: Mapped[UUIDType] = mapped_column(
        ForeignKey("zones.id", ondelete="CASCADE"), index=True
    )
    score: Mapped[int] = mapped_column(Integer)
    level: Mapped[str] = mapped_column(String(20), index=True)
    confidence: Mapped[int] = mapped_column(Integer)
    is_emergency_override: Mapped[bool] = mapped_column(Boolean, default=False)

    # list[dict] shaped like schemas.risk.CategoryRisk / RiskContributor respectively.
    categories: Mapped[list[dict]] = mapped_column(_JSONVariant)
    contributors: Mapped[list[dict]] = mapped_column(_JSONVariant)

    explanation: Mapped[str] = mapped_column(String(2000))

    engine_version: Mapped[str] = mapped_column(String(30))
    trigger_source: Mapped[str] = mapped_column(String(30), default="scheduler_tick")
    evaluation_duration_ms: Mapped[int] = mapped_column(Integer)

    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    zone: Mapped["Zone"] = relationship()
