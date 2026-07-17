from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID as UUIDType

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.equipment import Equipment
    from app.models.incident import Incident
    from app.models.permit import Permit
    from app.models.recommendation import Recommendation
    from app.models.risk_snapshot import RiskSnapshot
    from app.models.worker import Worker
    from app.models.zone import Zone


class Event(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A plain activity log entry (permit issued, equipment status changed, worker checked in, ...).
    This is deliberately generic and un-opinionated: the Operational Timeline is a filtered/
    sorted read-model composed over this table (plus RiskSnapshot/Recommendation/Incident), not
    a separate store of its own — see operational-timeline-architecture.md.

    risk_snapshot_id/incident_id are the explicit causal edges that let the Timeline (and later
    Root Cause Analysis) walk Sensor -> Rule -> RiskSnapshot -> Recommendation -> Incident ->
    Operator Action without re-deriving relationships from timestamps/rule_ids. actor_type
    distinguishes "the engine detected this" from "a person did this" — existing/internal
    emitters never pass it and get the "system" column default; only operator-facing actions
    (acknowledge, resolve, incident notes/escalate/close) pass actor_type="operator" explicitly.
    severity is derived server-side from event_type (see EventRepository.create), never
    supplied by a caller, so it can't drift out of sync with the taxonomy.
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
    recommendation_id: Mapped[UUIDType | None] = mapped_column(
        ForeignKey("recommendations.id"), index=True, nullable=True
    )
    risk_snapshot_id: Mapped[UUIDType | None] = mapped_column(
        ForeignKey("risk_snapshots.id"), index=True, nullable=True
    )
    incident_id: Mapped[UUIDType | None] = mapped_column(
        ForeignKey("incidents.id"), index=True, nullable=True
    )
    actor_type: Mapped[str] = mapped_column(String(20), default="system")
    actor_id: Mapped[UUIDType | None] = mapped_column(ForeignKey("workers.id"), index=True, nullable=True)

    event_type: Mapped[str] = mapped_column(String(50), index=True)
    severity: Mapped[str] = mapped_column(String(20), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String(2000))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    zone: Mapped["Zone | None"] = relationship(back_populates="events")
    equipment: Mapped["Equipment | None"] = relationship(back_populates="events")
    permit: Mapped["Permit | None"] = relationship(back_populates="events")
    recorded_by: Mapped["Worker | None"] = relationship(
        back_populates="recorded_events", foreign_keys=[recorded_by_id]
    )
    actor: Mapped["Worker | None"] = relationship(foreign_keys=[actor_id])
    recommendation: Mapped["Recommendation | None"] = relationship()
    risk_snapshot: Mapped["RiskSnapshot | None"] = relationship()
    incident: Mapped["Incident | None"] = relationship()
