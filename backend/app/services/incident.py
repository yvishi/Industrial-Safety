from datetime import datetime, timezone
from uuid import UUID

from app.core.exceptions import ConflictError, NotFoundError
from app.correlation_engine.config import CorrelationEngineConfig, DEFAULT_CORRELATION_CONFIG
from app.correlation_engine.decide import OpenIncidentSnapshot, ThresholdState, decide
from app.correlation_engine.narrative import NarrativeInput, generate_summary, generate_title
from app.models.incident import Incident
from app.models.recommendation import Recommendation
from app.repositories.event import EventRepository
from app.repositories.incident import IncidentRepository
from app.repositories.recommendation import RecommendationRepository
from app.repositories.zone import ZoneRepository
from app.risk_engine.config.schema import RiskLevel
from app.risk_engine.facts import ZoneFacts
from app.schemas.event import EventType
from app.schemas.incident import (
    IncidentClassification,
    IncidentCloseRequest,
    IncidentEscalateRequest,
    IncidentManualCreate,
    IncidentNoteCreate,
    IncidentOrigin,
    IncidentRead,
    IncidentSeverity,
    IncidentStatus,
)
from app.schemas.recommendation import RecommendationPriority
from app.schemas.risk import RiskAssessment

_PRIORITY_RANK: dict[str, int] = {"low": 0, "moderate": 1, "high": 2, "critical": 3}


def _highest_priority(rows: list[Recommendation]) -> RecommendationPriority | None:
    if not rows:
        return None
    best = max(rows, key=lambda r: _PRIORITY_RANK.get(r.priority, -1))
    return RecommendationPriority(best.priority)


def _top_recommendation(rows: list[Recommendation]) -> Recommendation | None:
    if not rows:
        return None
    return max(rows, key=lambda r: (_PRIORITY_RANK.get(r.priority, -1), r.last_seen_at))


def _build_narrative_input(
    *,
    zone_name: str,
    classification: str,
    risk_severity_at_open: str | None,
    status: str,
    opened_at: datetime,
    resolved_at: datetime | None,
    assessment: RiskAssessment | None,
    active_recommendations: list[Recommendation],
) -> NarrativeInput:
    top_contributor_rationale = None
    if assessment is not None and assessment.contributors:
        top_contributor_rationale = max(assessment.contributors, key=lambda c: c.impact).rationale

    top_rec = _top_recommendation(active_recommendations)
    return NarrativeInput(
        zone_name=zone_name,
        classification=classification,
        risk_severity_at_open=RiskLevel(risk_severity_at_open) if risk_severity_at_open else None,
        status=status,
        opened_at=opened_at,
        resolved_at=resolved_at,
        top_contributor_rationale=top_contributor_rationale,
        top_recommendation_title=top_rec.title if top_rec else None,
        recommendation_acknowledged=(top_rec.state == "acknowledged") if top_rec else False,
    )


def _narrative_input_for_existing(
    incident: Incident,
    assessment: RiskAssessment,
    active_recommendations: list[Recommendation],
    *,
    status: str,
    resolved_at: datetime | None,
) -> NarrativeInput:
    """Shared by _keep_open/_resolve — both narrate an already-open incident against the
    current tick's assessment, differing only in status/resolved_at."""
    return _build_narrative_input(
        zone_name=assessment.zone_name,
        classification=incident.classification,
        risk_severity_at_open=incident.risk_severity_at_open,
        status=status,
        opened_at=incident.opened_at,
        resolved_at=resolved_at,
        assessment=assessment,
        active_recommendations=active_recommendations,
    )


def _build_context_snapshot(facts: ZoneFacts, assessment: RiskAssessment) -> dict:
    """Filtered ZoneFacts + RiskAssessment — only what's outside its normal band, not a full
    dump of every nominal reading (that would be noise an investigator doesn't need and would
    needlessly bloat every row — see architecture Rev. 2, §R2.8)."""
    return {
        "sensors_outside_normal": [
            {
                "sensor_id": str(s.sensor_id),
                "tag_number": s.tag_number,
                "sensor_type": s.sensor_type,
                "last_value": s.last_value,
                "effective_band": s.effective_band,
            }
            for s in facts.sensors
            if s.effective_band not in ("normal", "unknown")
        ],
        "workers_present": [
            {"worker_id": str(w.worker_id), "employee_id": w.employee_id, "role": w.role}
            for w in facts.workers_present
        ],
        "active_permits": [
            {"permit_id": str(p.permit_id), "permit_number": p.permit_number, "permit_type": p.permit_type}
            for p in facts.active_permits
        ],
        "equipment_not_operational": [
            {"equipment_id": str(e.equipment_id), "tag_number": e.tag_number, "status": e.status}
            for e in facts.equipment
            if e.status != "operational"
        ],
        "categories": [c.model_dump(mode="json") for c in assessment.categories],
        "contributors": [c.model_dump(mode="json") for c in assessment.contributors],
    }


class IncidentService:
    """
    Bespoke orchestrator, like RiskService/RecommendationService: an Incident's system-detected
    path is always internally derived from correlation_engine.decide()'s output, never a
    user-submitted payload — only the narrow manual-create/note/escalate/close actions are.

    Deliberately does NOT own the per-zone debounce state decide() needs (see ThresholdState):
    IncidentService instances are short-lived (a fresh one is constructed every scheduler tick,
    and again per HTTP request via api/deps.py), so the only place that state can safely live is
    whichever object genuinely persists across ticks — RiskScheduler, the same way it already
    owns `self._running`. reconcile() takes the caller's threshold_states dict and mutates it in
    place; a request-scoped IncidentService that never calls reconcile() never touches it.
    """

    def __init__(
        self,
        repository: IncidentRepository,
        recommendation_repository: RecommendationRepository,
        event_repository: EventRepository,
        zone_repository: ZoneRepository,
        config: CorrelationEngineConfig = DEFAULT_CORRELATION_CONFIG,
    ) -> None:
        self.repository = repository
        self.recommendation_repository = recommendation_repository
        self.event_repository = event_repository
        self.zone_repository = zone_repository
        self.config = config

    # --- scheduler-driven correlation ---

    async def reconcile(
        self,
        assessment: RiskAssessment,
        facts: ZoneFacts,
        active_recommendations: list[Recommendation],
        threshold_states: dict[UUID, ThresholdState],
    ) -> Incident | None:
        """Called once per zone on every risk-evaluation tick, right after
        RecommendationService.reconcile() for that same zone (see RiskScheduler.run_once).
        `threshold_states` is owned by the caller (RiskScheduler) and mutated in place so the
        debounce counters survive across ticks without this service holding any state itself."""
        zone_id = assessment.zone_id
        open_incident = await self.repository.open_for_zone(zone_id)

        if open_incident is not None and open_incident.origin == IncidentOrigin.MANUAL.value:
            # Operator-owned: the Correlation Engine never auto-modifies, auto-resolves, or
            # opens a second incident over one a human has manually declared for this zone.
            return open_incident

        snapshot = (
            OpenIncidentSnapshot(peak_risk_severity=RiskLevel(open_incident.peak_risk_severity))
            if open_incident is not None
            else None
        )

        previous_state = threshold_states.get(zone_id, ThresholdState())
        new_state, decision = decide(
            level=assessment.level,
            is_emergency_override=assessment.is_emergency_override,
            highest_active_priority=_highest_priority(active_recommendations),
            current_incident=snapshot,
            previous_state=previous_state,
            config=self.config,
        )
        threshold_states[zone_id] = new_state

        if decision.action == "open":
            return await self._open(assessment, facts, active_recommendations, decision)
        if decision.action == "keep_open":
            return await self._keep_open(open_incident, assessment, active_recommendations, decision)
        if decision.action == "resolve":
            return await self._resolve(open_incident, assessment, active_recommendations)
        return open_incident  # action == "none"

    async def _open(self, assessment, facts, active_recommendations, decision) -> Incident:
        now = datetime.now(timezone.utc)
        narrative_input = _build_narrative_input(
            zone_name=facts.zone_name,
            classification=IncidentClassification.OPERATIONAL_EPISODE.value,
            risk_severity_at_open=assessment.level.value,
            status="open",
            opened_at=now,
            resolved_at=None,
            assessment=assessment,
            active_recommendations=active_recommendations,
        )
        incident = await self.repository.create(
            {
                "primary_zone_id": assessment.zone_id,
                "affected_zone_ids": [str(assessment.zone_id)],
                "status": IncidentStatus.OPEN.value,
                "origin": IncidentOrigin.SYSTEM_DETECTED.value,
                "classification": IncidentClassification.OPERATIONAL_EPISODE.value,
                "risk_severity_at_open": assessment.level.value,
                "peak_risk_severity": decision.peak_risk_severity.value,
                "incident_severity": None,
                "title": generate_title(narrative_input),
                "summary": generate_summary(narrative_input),
                "opened_context_snapshot": _build_context_snapshot(facts, assessment),
                "opened_at": now,
                "root_cause": None,
                "corrective_actions": [],
            }
        )
        # Retroactively attaches the specific risk-level-change event that triggered this
        # incident — it was logged by RiskService a step earlier in this same tick, before
        # this Incident existed for it to point to.
        await self.event_repository.link_recent_unlinked(
            assessment.zone_id,
            [EventType.RISK_LEVEL_INCREASED.value, EventType.RISK_LEVEL_DECREASED.value],
            incident.id,
        )
        await self._link_recommendations(incident, active_recommendations)
        await self._emit_lifecycle_event(incident, EventType.INCIDENT_OPENED, f"Incident opened: {incident.title}")
        return incident

    async def _keep_open(self, incident, assessment, active_recommendations, decision) -> Incident:
        narrative_input = _narrative_input_for_existing(
            incident, assessment, active_recommendations, status="open", resolved_at=None
        )
        new_summary = generate_summary(narrative_input)
        # decide()'s "keep_open" contract always sets peak_risk_severity — no None-guard needed.
        new_peak = decision.peak_risk_severity.value
        values: dict = {}
        if new_summary != incident.summary:
            values["summary"] = new_summary
        if new_peak != incident.peak_risk_severity:
            values["peak_risk_severity"] = new_peak
        updated = await self.repository.update(incident, values) if values else incident
        await self._link_recommendations(updated, active_recommendations)
        return updated

    async def _resolve(self, incident, assessment, active_recommendations) -> Incident:
        now = datetime.now(timezone.utc)
        narrative_input = _narrative_input_for_existing(
            incident, assessment, active_recommendations, status="resolved", resolved_at=now
        )
        updated = await self.repository.update(
            incident,
            {
                "status": IncidentStatus.RESOLVED.value,
                "resolved_at": now,
                "summary": generate_summary(narrative_input),
            },
        )
        # A recommendation can legitimately become active on the very tick the incident
        # resolves (a late-triggering rule) — link it before this incident stops being "current".
        await self._link_recommendations(updated, active_recommendations)
        await self._emit_lifecycle_event(updated, EventType.INCIDENT_RESOLVED, f"Incident resolved: {updated.title}")
        return updated

    async def _link_recommendations(self, incident: Incident, active_recommendations: list[Recommendation]) -> None:
        unlinked_ids = [row.id for row in active_recommendations if row.incident_id != incident.id]
        if not unlinked_ids:
            return
        await self.recommendation_repository.link_to_incident(unlinked_ids, incident.id)
        # The recommendation_created event for each of these fired one service earlier in the
        # same tick, before this Incident existed — backfill it now that we know the link.
        await self.event_repository.link_by_recommendation_ids(unlinked_ids, incident.id)
        for row in active_recommendations:
            if row.id in unlinked_ids:
                row.incident_id = incident.id

    async def _emit_lifecycle_event(
        self,
        incident: Incident,
        event_type: EventType,
        title: str,
        *,
        description: str | None = None,
        actor_type: str = "system",
        actor_id: UUID | None = None,
    ) -> None:
        await self.event_repository.create(
            {
                "zone_id": incident.primary_zone_id,
                "incident_id": incident.id,
                "event_type": event_type.value,
                "title": title,
                "description": description,
                "actor_type": actor_type,
                "actor_id": actor_id,
                "occurred_at": datetime.now(timezone.utc),
            }
        )

    # --- operator-facing actions ---

    async def create_manual(self, payload: IncidentManualCreate) -> IncidentRead:
        existing = await self.repository.open_for_zone(payload.primary_zone_id)
        if existing is not None:
            raise ConflictError(
                f"Zone already has an open incident ('{existing.title}'); resolve or close it first"
            )

        now = datetime.now(timezone.utc)
        incident = await self.repository.create(
            {
                "primary_zone_id": payload.primary_zone_id,
                "affected_zone_ids": [str(payload.primary_zone_id)],
                "status": IncidentStatus.OPEN.value,
                "origin": IncidentOrigin.MANUAL.value,
                "classification": payload.classification.value,
                "risk_severity_at_open": None,
                "peak_risk_severity": None,
                "incident_severity": None,
                "title": payload.title,
                "summary": payload.description,
                "opened_context_snapshot": None,
                "opened_at": now,
                "root_cause": None,
                "corrective_actions": [],
                "opened_by_id": payload.opened_by_id,
            }
        )
        await self._emit_lifecycle_event(
            incident,
            EventType.INCIDENT_OPENED,
            f"Incident manually declared: {incident.title}",
            actor_type="operator",
            actor_id=payload.opened_by_id,
        )
        return await self._to_read_with_zone_name(incident)

    async def add_note(self, incident_id: UUID, payload: IncidentNoteCreate) -> IncidentRead:
        incident = await self._get_or_404(incident_id)
        self._ensure_not_closed(incident)
        await self._emit_lifecycle_event(
            incident,
            EventType.INCIDENT_NOTE_ADDED,
            f"Note added to incident: {incident.title}",
            description=payload.note_text,
            actor_type="operator",
            actor_id=payload.actor_id,
        )
        return await self._to_read_with_zone_name(incident)

    async def escalate(self, incident_id: UUID, payload: IncidentEscalateRequest) -> IncidentRead:
        incident = await self._get_or_404(incident_id)
        self._ensure_not_closed(incident)
        updated = await self.repository.update(incident, {"classification": payload.classification.value})
        await self._emit_lifecycle_event(
            updated,
            EventType.INCIDENT_ESCALATED,
            f"Incident reclassified to {payload.classification.value}: {updated.title}",
            actor_type="operator",
            actor_id=payload.actor_id,
        )
        return await self._to_read_with_zone_name(updated)

    async def close(self, incident_id: UUID, payload: IncidentCloseRequest) -> IncidentRead:
        incident = await self._get_or_404(incident_id)
        self._ensure_not_closed(incident)
        if incident.classification == IncidentClassification.REPORTABLE_INCIDENT.value and (
            not payload.root_cause or payload.incident_severity is None
        ):
            raise ConflictError("root_cause and incident_severity are required to close a reportable_incident")

        now = datetime.now(timezone.utc)
        values: dict = {
            "status": IncidentStatus.CLOSED.value,
            "closed_at": now,
            "closed_by_id": payload.actor_id,
            "corrective_actions": payload.corrective_actions,
        }
        if incident.resolved_at is None:
            # Manual incidents have no automatic resolve step to pass through first.
            values["resolved_at"] = now
        if payload.root_cause is not None:
            values["root_cause"] = payload.root_cause
        if payload.incident_severity is not None:
            values["incident_severity"] = payload.incident_severity.value

        updated = await self.repository.update(incident, values)
        await self._emit_lifecycle_event(
            updated,
            EventType.INCIDENT_CLOSED,
            f"Incident closed: {updated.title}",
            actor_type="operator",
            actor_id=payload.actor_id,
        )
        return await self._to_read_with_zone_name(updated)

    def _ensure_not_closed(self, incident: Incident) -> None:
        if incident.status == IncidentStatus.CLOSED.value:
            raise ConflictError(f"Incident '{incident.id}' is already closed")

    # --- reads ---

    async def get(self, incident_id: UUID) -> IncidentRead:
        incident = await self._get_or_404(incident_id)
        return await self._to_read_with_zone_name(incident)

    async def list_incidents(
        self,
        *,
        zone_id: UUID | None = None,
        status: str | None = None,
        classification: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[IncidentRead], int]:
        items, total = await self.repository.list(
            page=page,
            page_size=page_size,
            primary_zone_id=zone_id,
            status=status,
            classification=classification,
        )
        zone_cache: dict[UUID, str] = {}
        reads = []
        for row in items:
            if row.primary_zone_id not in zone_cache:
                zone_cache[row.primary_zone_id] = await self._zone_name(row.primary_zone_id)
            reads.append(self._to_read(row, zone_cache[row.primary_zone_id]))
        return reads, total

    async def _get_or_404(self, incident_id: UUID) -> Incident:
        row = await self.repository.get_by_id(incident_id)
        if row is None:
            raise NotFoundError(f"Incident '{incident_id}' not found")
        return row

    async def _zone_name(self, zone_id: UUID) -> str:
        zone = await self.zone_repository.get_by_id(zone_id)
        return zone.name if zone is not None else ""

    async def _to_read_with_zone_name(self, row: Incident) -> IncidentRead:
        return self._to_read(row, await self._zone_name(row.primary_zone_id))

    def _to_read(self, row: Incident, zone_name: str) -> IncidentRead:
        return IncidentRead(
            id=row.id,
            created_at=row.created_at,
            updated_at=row.updated_at,
            primary_zone_id=row.primary_zone_id,
            zone_name=zone_name,
            affected_zone_ids=list(row.affected_zone_ids),
            status=IncidentStatus(row.status),
            origin=IncidentOrigin(row.origin),
            classification=IncidentClassification(row.classification),
            risk_severity_at_open=RiskLevel(row.risk_severity_at_open) if row.risk_severity_at_open else None,
            peak_risk_severity=RiskLevel(row.peak_risk_severity) if row.peak_risk_severity else None,
            incident_severity=IncidentSeverity(row.incident_severity) if row.incident_severity else None,
            title=row.title,
            summary=row.summary,
            opened_at=row.opened_at,
            resolved_at=row.resolved_at,
            closed_at=row.closed_at,
            root_cause=row.root_cause,
            corrective_actions=list(row.corrective_actions),
            opened_by_id=row.opened_by_id,
            closed_by_id=row.closed_by_id,
        )
