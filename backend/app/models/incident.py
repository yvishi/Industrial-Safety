from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID as UUIDType

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.worker import Worker
    from app.models.zone import Zone

# Real JSONB on Postgres; falls back to JSON (TEXT-backed) on SQLite for the in-memory test
# database — same dual-dialect convention as risk_snapshot.py/recommendation.py.
_JSONVariant = JSON().with_variant(JSONB(), "postgresql")


class Incident(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A bounded, ownable episode of elevated risk in one zone — the Correlation Engine's
    persisted output (see app/correlation_engine/decide.py for the pure decision logic this
    lifecycle is driven by). Deliberately distinct from RiskSnapshot (a frozen point-in-time
    fact) and Recommendation (one condition's own lifecycle): an Incident is the thing an
    operator can point to and say "that's over now" about a zone as a whole, and the unit
    Reports/Compliance Audits/Root Cause Analysis attach to later.

    `origin` distinguishes system-detected episodes (opened by the Correlation Engine) from
    manually-declared ones (an operator logging something the sensors never saw at all, e.g. a
    slip-and-fall — which is also why risk_severity_at_open/peak_risk_severity/
    opened_context_snapshot are nullable: a manual incident has no RiskAssessment/ZoneFacts
    behind it at all). `classification` distinguishes routine operational episodes — most of
    which resolve uneventfully — from ones carrying real regulatory weight
    (reportable_incident), so the same lifecycle machinery serves both without a second entity
    or a compliance system flooded with noise.

    `incident_severity` is a deliberately separate axis from risk_severity_at_open/
    peak_risk_severity: risk severity is a computed hazard/potential-danger metric,
    incident_severity is an operator's assessment of actual real-world impact (a Critical-risk
    incident handled immediately with no damage may only be Moderate impact) — never derived
    algorithmically, only ever set by a human at close() time.

    Lifecycle: OPEN -> RESOLVED -> CLOSED. OPEN -> RESOLVED is automatic for system-detected
    incidents (Correlation Engine, mirroring Recommendation's own auto-resolve-on-reconcile).
    RESOLVED -> CLOSED (or OPEN -> CLOSED directly, for manual incidents with no correlation
    loop to resolve them automatically) is a deliberate human confirmation step, gated on
    root_cause + incident_severity when classification=reportable_incident. A resolved incident
    can reopen if the same condition recurs before closure — the same partial-unique-index
    treatment that fixed the Recommendation Engine's real recurring-identity_key bug, scoped
    here to "one OPEN incident per zone" instead of a recurring key. CLOSED is terminal by
    design — corrections are new rows, not edits to a closed one, the same posture RiskSnapshot's
    frozen facts already take.
    """

    __tablename__ = "incidents"

    primary_zone_id: Mapped[UUIDType] = mapped_column(
        ForeignKey("zones.id", ondelete="CASCADE"), index=True
    )
    # Inert in v1: no cross-zone correlation scenario exists yet (single-zone simulator), so
    # this is always exactly [primary_zone_id] at open and never touched again. Kept only so a
    # future multi-zone incident doesn't need a schema change (architecture Rev. 2, §R2.7 —
    # same "reserved, not built" treatment as a future merged_into_id self-FK).
    affected_zone_ids: Mapped[list[str]] = mapped_column(_JSONVariant, default=list)

    status: Mapped[str] = mapped_column(String(20), index=True, default="open")
    origin: Mapped[str] = mapped_column(String(20), index=True)
    classification: Mapped[str] = mapped_column(String(30), index=True, default="operational_episode")

    # Nullable: unset for origin="manual" (no RiskAssessment exists behind it).
    risk_severity_at_open: Mapped[str | None] = mapped_column(String(20), nullable=True)
    peak_risk_severity: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # Operator-set only; required at close() when classification=reportable_incident.
    incident_severity: Mapped[str | None] = mapped_column(String(20), nullable=True)

    title: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(String(2000))

    # Filtered ZoneFacts + RiskAssessment, captured once at open from data already computed
    # that tick — never updated afterward (see IncidentService), never populated for
    # origin="manual".
    opened_context_snapshot: Mapped[dict | None] = mapped_column(_JSONVariant, nullable=True)

    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    root_cause: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    corrective_actions: Mapped[list[str]] = mapped_column(_JSONVariant, default=list)

    opened_by_id: Mapped[UUIDType | None] = mapped_column(
        ForeignKey("workers.id"), index=True, nullable=True
    )
    closed_by_id: Mapped[UUIDType | None] = mapped_column(
        ForeignKey("workers.id"), index=True, nullable=True
    )

    zone: Mapped["Zone"] = relationship(foreign_keys=[primary_zone_id])
    opened_by: Mapped["Worker | None"] = relationship(foreign_keys=[opened_by_id])
    closed_by: Mapped["Worker | None"] = relationship(foreign_keys=[closed_by_id])

    __table_args__ = (
        Index(
            "ux_incidents_primary_zone_id_open",
            "primary_zone_id",
            unique=True,
            postgresql_where=text("status = 'open'"),
            sqlite_where=text("status = 'open'"),
        ),
        Index("ix_incidents_primary_zone_id_opened_at", "primary_zone_id", "opened_at"),
    )
