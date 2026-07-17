from datetime import datetime, timezone
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.models.recommendation import Recommendation
from app.recommendation_engine import ENGINE_VERSION
from app.recommendation_engine.generator import RecommendationCandidate, generate_candidates
from app.recommendation_engine.templates import RULE_TEMPLATE_MAP, TEMPLATES
from app.repositories.event import EventRepository
from app.repositories.recommendation import RecommendationRepository
from app.repositories.risk import RiskRepository
from app.repositories.zone import ZoneRepository
from app.schemas.event import EventType
from app.schemas.recommendation import (
    PlantRecommendationSummary,
    RecommendationPriority,
    RecommendationRead,
    RecommendationState,
    RecommendationTemplateEntry,
)
from app.schemas.risk import EntityRefRead, RiskAssessment

# Cross-zone Action Queue is deliberately capped short — it exists to answer "what should I do
# right now" at a glance, not to reproduce every active recommendation plant-wide.
PLANT_QUEUE_LIMIT = 8

_PRIORITY_RANK: dict[str, int] = {"critical": 0, "high": 1, "moderate": 2, "low": 3}


def build_template_catalog() -> list[RecommendationTemplateEntry]:
    """Static template catalog for GET /api/v1/recommendations/templates — introspects the
    rule_id -> template mapping, touches no DB. Mirrors build_rule_catalog in services/risk.py."""
    source_rules: dict[str, list[str]] = {}
    for rule_id, template_id in RULE_TEMPLATE_MAP.items():
        source_rules.setdefault(template_id, []).append(rule_id)

    return [
        RecommendationTemplateEntry(
            template_id=template.template_id,
            category=template.category,
            title=template.title,
            action_text=template.action_text,
            expected_outcomes=list(template.expected_outcomes),
            target_entity_type=template.target_entity_type,
            source_rule_ids=sorted(source_rules.get(template.template_id, [])),
        )
        for template in TEMPLATES.values()
    ]


class RecommendationService:
    """
    Bespoke orchestrator — not a BaseService[Recommendation] subclass, for the same reason
    RiskService isn't a BaseService[RiskSnapshot]: a Recommendation is never created from a
    user-submitted payload, only ever internally derived by reconcile(). The only
    user-submitted operations are the two narrow state transitions (acknowledge/resolve).
    """

    def __init__(
        self,
        repository: RecommendationRepository,
        zone_repository: ZoneRepository,
        event_repository: EventRepository,
        risk_repository: RiskRepository,
    ) -> None:
        self.repository = repository
        self.zone_repository = zone_repository
        self.event_repository = event_repository
        self.risk_repository = risk_repository

    async def reconcile(self, assessment: RiskAssessment) -> list[Recommendation]:
        """Called once per zone on every risk-evaluation tick (see RiskScheduler). Diffs freshly
        generated candidates against this zone's currently-open rows, keyed by a stable
        identity (zone_id + template_id): new candidates are inserted as NEW, still-matching
        ones are touched in place (last_seen_at/priority/rationale/target), and open rows with
        no matching candidate this cycle auto-resolve, because the condition that produced them
        no longer holds. Returns the post-reconcile active set (created + touched rows, in no
        particular order) so the Correlation Engine can read it in the same tick without a
        redundant re-query — see IncidentService.reconcile."""
        now = datetime.now(timezone.utc)
        candidates = generate_candidates(assessment)
        candidates_by_key = {f"{assessment.zone_id}:{c.template_id}": c for c in candidates}

        open_rows = await self.repository.active_for_zone(assessment.zone_id)
        open_by_key = {row.identity_key: row for row in open_rows}

        # "Nearest known" snapshot for this zone, not necessarily persisted this exact tick —
        # CRE only persists on meaningful change, so a recommendation created on a non-persisting
        # tick still gets a real (if slightly earlier) frozen assessment to point back to.
        latest_snapshot = await self.risk_repository.latest_for_zone(assessment.zone_id)
        triggering_snapshot_id = latest_snapshot.id if latest_snapshot is not None else None

        active: list[Recommendation] = []
        for identity_key, candidate in candidates_by_key.items():
            existing = open_by_key.get(identity_key)
            if existing is None:
                created = await self.repository.create(
                    self._candidate_to_values(
                        assessment.zone_id, candidate, identity_key, now, triggering_snapshot_id
                    )
                )
                await self._emit_created_event(created)
                active.append(created)
            else:
                updated = await self.repository.update(
                    existing,
                    {
                        "priority": candidate.priority,
                        "rationale": candidate.rationale,
                        "source_rule_ids": list(candidate.source_rule_ids),
                        "target_entity": candidate.target_entity.model_dump(mode="json"),
                        "last_seen_at": now,
                    },
                )
                active.append(updated)

        for identity_key, row in open_by_key.items():
            if identity_key not in candidates_by_key:
                await self._resolve(row, reason="Underlying condition cleared.")

        return active

    async def _emit_created_event(self, row: Recommendation) -> None:
        await self.event_repository.create(
            {
                "zone_id": row.zone_id,
                "recommendation_id": row.id,
                "risk_snapshot_id": row.triggering_snapshot_id,
                "event_type": EventType.RECOMMENDATION_CREATED.value,
                "title": f"Recommendation created: {row.title}",
                "description": None,
                "occurred_at": row.first_generated_at,
            }
        )

    async def get_zone_recommendations(
        self, zone_id: UUID, *, include_resolved: bool = False
    ) -> list[RecommendationRead]:
        rows = (
            await self.repository.all_for_zone(zone_id)
            if include_resolved
            else await self.repository.active_for_zone(zone_id)
        )
        zone_name = await self._zone_name(zone_id)
        reads = [self._to_read(row, zone_name) for row in rows]
        reads.sort(key=lambda r: (_PRIORITY_RANK.get(r.priority.value, 9), r.last_seen_at), reverse=False)
        return reads

    async def get_plant_summary(self) -> PlantRecommendationSummary:
        rows = await self.repository.all_active()
        zone_cache: dict[UUID, str] = {}
        reads: list[RecommendationRead] = []
        for row in rows:
            if row.zone_id not in zone_cache:
                zone_cache[row.zone_id] = await self._zone_name(row.zone_id)
            reads.append(self._to_read(row, zone_cache[row.zone_id]))

        reads.sort(key=lambda r: (_PRIORITY_RANK.get(r.priority.value, 9), r.last_seen_at))
        counts: dict[str, int] = {}
        for read in reads:
            counts[read.priority.value] = counts.get(read.priority.value, 0) + 1

        return PlantRecommendationSummary(
            generated_at=datetime.now(timezone.utc),
            top_recommendations=reads[:PLANT_QUEUE_LIMIT],
            counts_by_priority=counts,
            plant_wide_emergency_active=any(r.priority == RecommendationPriority.CRITICAL for r in reads),
        )

    async def history_for_zone(
        self, zone_id: UUID, *, page: int = 1, page_size: int = 50
    ) -> tuple[list[RecommendationRead], int]:
        items, total = await self.repository.list(page=page, page_size=page_size, zone_id=zone_id)
        zone_name = await self._zone_name(zone_id)
        return [self._to_read(item, zone_name) for item in items], total

    async def acknowledge(self, recommendation_id: UUID) -> RecommendationRead:
        row = await self._get_or_404(recommendation_id)
        if row.state == RecommendationState.NEW.value:
            row = await self.repository.update(
                row,
                {
                    "state": RecommendationState.ACKNOWLEDGED.value,
                    "acknowledged_at": datetime.now(timezone.utc),
                },
            )
            await self.event_repository.create(
                {
                    "zone_id": row.zone_id,
                    "recommendation_id": row.id,
                    "event_type": EventType.RECOMMENDATION_ACKNOWLEDGED.value,
                    "title": f"Recommendation acknowledged: {row.title}",
                    "description": None,
                    "occurred_at": datetime.now(timezone.utc),
                }
            )
        return self._to_read(row, await self._zone_name(row.zone_id))

    async def resolve(self, recommendation_id: UUID) -> RecommendationRead:
        row = await self._get_or_404(recommendation_id)
        row = await self._resolve(row, reason="Marked resolved by operator.")
        return self._to_read(row, await self._zone_name(row.zone_id))

    async def _resolve(self, row: Recommendation, *, reason: str) -> Recommendation:
        updated = await self.repository.update(
            row, {"state": RecommendationState.RESOLVED.value, "resolved_at": datetime.now(timezone.utc)}
        )
        await self.event_repository.create(
            {
                "zone_id": updated.zone_id,
                "recommendation_id": updated.id,
                "event_type": EventType.RECOMMENDATION_RESOLVED.value,
                "title": f"Recommendation resolved: {updated.title}",
                "description": reason,
                "occurred_at": datetime.now(timezone.utc),
            }
        )
        return updated

    async def _get_or_404(self, recommendation_id: UUID) -> Recommendation:
        row = await self.repository.get_by_id(recommendation_id)
        if row is None:
            raise NotFoundError(f"Recommendation '{recommendation_id}' not found")
        return row

    async def _zone_name(self, zone_id: UUID) -> str:
        zone = await self.zone_repository.get_by_id(zone_id)
        return zone.name if zone is not None else ""

    def _candidate_to_values(
        self,
        zone_id: UUID,
        candidate: RecommendationCandidate,
        identity_key: str,
        now: datetime,
        triggering_snapshot_id: UUID | None,
    ) -> dict:
        return {
            "zone_id": zone_id,
            "triggering_snapshot_id": triggering_snapshot_id,
            "identity_key": identity_key,
            "template_id": candidate.template_id,
            "category": candidate.category.value,
            "priority": candidate.priority,
            "state": RecommendationState.NEW.value,
            "title": candidate.title,
            "action_text": candidate.action_text,
            "expected_outcomes": list(candidate.expected_outcomes),
            "rationale": candidate.rationale,
            "source_rule_ids": list(candidate.source_rule_ids),
            "target_entity": candidate.target_entity.model_dump(mode="json"),
            "engine_version": ENGINE_VERSION,
            "generation_source": "deterministic",
            "first_generated_at": now,
            "last_seen_at": now,
        }

    def _to_read(self, row: Recommendation, zone_name: str) -> RecommendationRead:
        return RecommendationRead(
            id=row.id,
            created_at=row.created_at,
            updated_at=row.updated_at,
            zone_id=row.zone_id,
            zone_name=zone_name,
            incident_id=row.incident_id,
            template_id=row.template_id,
            category=row.category,
            priority=RecommendationPriority(row.priority),
            state=RecommendationState(row.state),
            title=row.title,
            action_text=row.action_text,
            expected_outcomes=row.expected_outcomes,
            rationale=row.rationale,
            source_rule_ids=row.source_rule_ids,
            target_entity=EntityRefRead(**row.target_entity),
            engine_version=row.engine_version,
            generation_source=row.generation_source,
            first_generated_at=row.first_generated_at,
            last_seen_at=row.last_seen_at,
            acknowledged_at=row.acknowledged_at,
            resolved_at=row.resolved_at,
        )
