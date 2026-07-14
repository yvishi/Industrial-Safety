from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID as UUIDType

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.zone import Zone

# Real JSONB on Postgres; falls back to JSON (TEXT-backed) on SQLite for the in-memory test
# database — same dual-dialect convention as risk_snapshot.py.
_JSONVariant = JSON().with_variant(JSONB(), "postgresql")


class Recommendation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A Recommendation Engine output: an operator-facing action derived from one or more
    currently-triggered Compound Risk Engine rules that share a recommendation template.

    Unlike RiskSnapshot (a frozen point-in-time fact), a Recommendation has a lifecycle:
    `identity_key` (zone_id + template_id) is stable across evaluation ticks, so the same row
    is updated in place (last_seen_at, priority, rationale) while its condition persists,
    rather than a new row being created every tick. It only leaves the "active" set by
    transitioning `state` to resolved — either automatically, when reconcile() finds no
    matching candidate for it anymore, or by an operator explicitly marking it resolved.
    v1 has no "dismissed" state: an operator who chooses not to act acknowledges instead,
    and the recommendation stays visible until the underlying condition actually clears.

    identity_key is deliberately unique only among non-resolved rows (a partial index below),
    not globally: the same condition legitimately recurs after resolving — a lone worker
    leaves and comes back, an ESD flag clears and re-trips — and each recurrence is a new
    lifecycle episode that deserves its own row and its own history, not a collision.
    """

    __tablename__ = "recommendations"

    zone_id: Mapped[UUIDType] = mapped_column(ForeignKey("zones.id", ondelete="CASCADE"), index=True)
    identity_key: Mapped[str] = mapped_column(String(150), index=True)
    template_id: Mapped[str] = mapped_column(String(60), index=True)
    category: Mapped[str] = mapped_column(String(30), index=True)
    priority: Mapped[str] = mapped_column(String(20), index=True)
    state: Mapped[str] = mapped_column(String(20), index=True, default="new")

    title: Mapped[str] = mapped_column(String(120))
    action_text: Mapped[str] = mapped_column(String(500))
    expected_outcomes: Mapped[list[str]] = mapped_column(_JSONVariant)
    rationale: Mapped[str] = mapped_column(String(500))
    source_rule_ids: Mapped[list[str]] = mapped_column(_JSONVariant)
    # EntityRefRead-shaped: {"entity_type": ..., "entity_id": ..., "label": ...}
    target_entity: Mapped[dict] = mapped_column(_JSONVariant)

    engine_version: Mapped[str] = mapped_column(String(30))
    # "deterministic" in v1 — reserved so a future LLM-assisted recommendation rule can coexist
    # and be distinguished without a migration.
    generation_source: Mapped[str] = mapped_column(String(20), default="deterministic")

    first_generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    zone: Mapped["Zone"] = relationship()

    __table_args__ = (
        Index(
            "ux_recommendations_identity_key_active",
            "identity_key",
            unique=True,
            postgresql_where=text("state != 'resolved'"),
            sqlite_where=text("state != 'resolved'"),
        ),
    )
