from datetime import datetime, timezone
from uuid import UUID

from app.ai.context.schemas import AIContext, AIContextScope, ContextSection
from app.core.exceptions import NotFoundError
from app.models.event import Event
from app.models.incident import Incident
from app.models.recommendation import Recommendation
from app.repositories.event import EventRepository
from app.repositories.incident import IncidentRepository
from app.repositories.recommendation import RecommendationRepository
from app.repositories.zone import ZoneRepository


class ContextBuilder:
    """
    The single place responsible for assembling structured operational context for the AI
    layer. Each scope (currently just "incident") gathers the handful of already-existing
    records that answer that kind of question and flattens them into one AIContext — e.g. "why
    did Incident #42 happen?" needs the Incident itself, its Timeline, the Risk Assessment
    captured when it opened, its Recommendations, and its Resolution.

    Deliberately reads through the existing repositories only — no new tables, no denormalized
    read-model, no vector search (this is all structured operational data; see the AI module's
    docstring for where semantic/document retrieval fits in later). Adding a new scope means
    adding one `build_*_context` method here; nothing about app.ai.prompts or app.ai.providers
    changes.
    """

    def __init__(
        self,
        incident_repository: IncidentRepository,
        event_repository: EventRepository,
        recommendation_repository: RecommendationRepository,
        zone_repository: ZoneRepository,
    ) -> None:
        self.incident_repository = incident_repository
        self.event_repository = event_repository
        self.recommendation_repository = recommendation_repository
        self.zone_repository = zone_repository

    async def build_incident_context(self, incident_id: UUID) -> AIContext:
        incident = await self.incident_repository.get_by_id(incident_id)
        if incident is None:
            raise NotFoundError(f"Incident '{incident_id}' not found")

        zone = await self.zone_repository.get_by_id(incident.primary_zone_id)
        zone_name = zone.name if zone is not None else "Unknown zone"

        events, _ = await self.event_repository.list(incident_id=incident_id, page_size=200)
        recommendations, _ = await self.recommendation_repository.list(incident_id=incident_id, page_size=50)

        sections = [
            self._incident_section(incident, zone_name),
            self._timeline_section(events),
            self._risk_assessment_section(incident),
            self._recommendations_section(recommendations),
            self._resolution_section(incident),
        ]

        return AIContext(
            scope=AIContextScope.INCIDENT,
            entity_id=incident_id,
            generated_at=datetime.now(timezone.utc),
            sections=sections,
        )

    def _incident_section(self, incident: Incident, zone_name: str) -> ContextSection:
        data = {
            "title": incident.title,
            "zone_name": zone_name,
            "status": incident.status,
            "origin": incident.origin,
            "classification": incident.classification,
            "risk_severity_at_open": incident.risk_severity_at_open,
            "peak_risk_severity": incident.peak_risk_severity,
            "opened_at": incident.opened_at.isoformat(),
            "summary": incident.summary,
        }
        content = (
            f"Title: {incident.title}\n"
            f"Zone: {zone_name}\n"
            f"Status: {incident.status} | Classification: {incident.classification} | Origin: {incident.origin}\n"
            f"Risk severity at open: {incident.risk_severity_at_open or 'n/a'} | "
            f"Peak risk severity: {incident.peak_risk_severity or 'n/a'}\n"
            f"Opened at: {incident.opened_at.isoformat()}\n"
            f"Summary: {incident.summary}"
        )
        return ContextSection(title="Incident", content=content, data=data)

    def _timeline_section(self, events: list[Event]) -> ContextSection:
        if not events:
            return ContextSection(title="Timeline", content="No timeline events recorded.", data={"events": []})

        ordered = sorted(events, key=lambda e: e.occurred_at)
        content = "\n".join(f"- {e.occurred_at.isoformat()} [{e.severity}] {e.title}" for e in ordered)
        data = {
            "events": [
                {
                    "occurred_at": e.occurred_at.isoformat(),
                    "event_type": e.event_type,
                    "severity": e.severity,
                    "title": e.title,
                }
                for e in ordered
            ]
        }
        return ContextSection(title="Timeline", content=content, data=data)

    def _risk_assessment_section(self, incident: Incident) -> ContextSection:
        snapshot = incident.opened_context_snapshot
        if not snapshot:
            return ContextSection(
                title="Risk Assessment",
                content="No risk assessment captured (manually declared incident).",
                data={},
            )

        lines = [f"Risk level at open: {incident.risk_severity_at_open or 'n/a'}"]

        contributors = snapshot.get("contributors", [])
        if contributors:
            lines.append("Contributing factors:")
            lines.extend(f"- {c.get('rationale') or c.get('factor', '')}" for c in contributors)

        sensors = snapshot.get("sensors_outside_normal", [])
        if sensors:
            lines.append("Sensors outside normal band:")
            lines.extend(f"- {s['tag_number']}: {s['last_value']} ({s['effective_band']})" for s in sensors)

        return ContextSection(title="Risk Assessment", content="\n".join(lines), data=snapshot)

    def _recommendations_section(self, recommendations: list[Recommendation]) -> ContextSection:
        if not recommendations:
            return ContextSection(
                title="Recommendations", content="No recommendations were issued.", data={"recommendations": []}
            )

        content = "\n".join(f"- [{r.priority}/{r.state}] {r.title}: {r.action_text}" for r in recommendations)
        data = {
            "recommendations": [
                {
                    "template_id": r.template_id,
                    "priority": r.priority,
                    "state": r.state,
                    "title": r.title,
                    "action_text": r.action_text,
                }
                for r in recommendations
            ]
        }
        return ContextSection(title="Recommendations", content=content, data=data)

    def _resolution_section(self, incident: Incident) -> ContextSection:
        if incident.resolved_at is None:
            return ContextSection(title="Resolution", content="Incident is still open.", data={"resolved": False})

        lines = [f"Resolved at: {incident.resolved_at.isoformat()}"]
        if incident.closed_at:
            lines.append(f"Closed at: {incident.closed_at.isoformat()}")
        if incident.root_cause:
            lines.append(f"Root cause: {incident.root_cause}")
        if incident.corrective_actions:
            lines.append("Corrective actions: " + "; ".join(incident.corrective_actions))

        data = {
            "resolved": True,
            "resolved_at": incident.resolved_at.isoformat(),
            "closed_at": incident.closed_at.isoformat() if incident.closed_at else None,
            "root_cause": incident.root_cause,
            "corrective_actions": list(incident.corrective_actions),
        }
        return ContextSection(title="Resolution", content="\n".join(lines), data=data)
