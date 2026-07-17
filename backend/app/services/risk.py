import time
from datetime import datetime, timezone
from uuid import UUID

from app.models.risk_snapshot import RiskSnapshot
from app.repositories.event import EventRepository
from app.repositories.risk import RiskRepository
from app.risk_engine import ENGINE_VERSION
from app.risk_engine.config.defaults import DEFAULT_RISK_CONFIG
from app.risk_engine.config.schema import RiskEngineConfig, RiskLevel
from app.risk_engine.engine.aggregator import aggregate, build_category_breakdown
from app.risk_engine.engine.confidence import compute_confidence, confidence_label_for
from app.risk_engine.engine.explain import generate_explanation
from app.risk_engine.engine.trend import compute_trend
from app.risk_engine.facts import ZoneFacts
from app.risk_engine.facts_builder import ZoneFactsBuilder
from app.risk_engine.rules import ALL_RULES
from app.risk_engine.rules.base import RuleResult
from app.schemas.event import EventType
from app.schemas.risk import (
    CategoryRisk,
    EntityRefRead,
    PlantRiskSummary,
    RecommendedAction,
    RiskAssessment,
    RiskContributor,
    RiskSnapshotRead,
    RuleCatalogEntry,
)

TRIGGER_SOURCE_SCHEDULER = "scheduler_tick"
# A snapshot is only persisted when the level changes or the score moves by more than this.
SCORE_DELTA_PERSIST_THRESHOLD = 10

_RISK_LEVEL_RANK: dict[str, int] = {level.value: i for i, level in enumerate(RiskLevel)}


def build_rule_catalog(config: RiskEngineConfig = DEFAULT_RISK_CONFIG) -> list[RuleCatalogEntry]:
    """Static rule catalog for GET /api/v1/risk/rules — introspects config, touches no DB."""
    return [
        RuleCatalogEntry(
            rule_id=rule.rule_id,
            category=rule.category,
            description=rule.description,
            default_severity=rule.default_severity,
            weight=config.rule_weights.weights.get(rule.rule_id, 0),
            is_emergency_override=rule.rule_id in config.emergency.emergency_rule_ids,
            suggested_action=rule.suggested_action,
        )
        for rule in ALL_RULES
    ]


class RiskService:
    """
    Bespoke cross-entity aggregator — like StateService, not a BaseService[RiskSnapshot]
    subclass, since a RiskSnapshot's "create" path is always internally derived (never a
    user-submitted Pydantic payload) and there is no single-entity CRUD lifecycle here.

    "Current" assessments (assess_zone/assess_plant) always live-compute against fresh
    ZoneFacts, matching StateService's "no caching" philosophy — toggling the ESD flag is
    reflected immediately rather than waiting for the next scheduler pass. "History"/"changes"
    read the persisted risk_snapshots table, which only has rows for meaningful transitions.
    """

    def __init__(
        self,
        repository: RiskRepository,
        facts_builder: ZoneFactsBuilder,
        event_repository: EventRepository,
        config: RiskEngineConfig = DEFAULT_RISK_CONFIG,
    ) -> None:
        self.repository = repository
        self.facts_builder = facts_builder
        self.event_repository = event_repository
        self.config = config

    async def assess_zone(self, zone_id: UUID) -> RiskAssessment:
        facts = await self.facts_builder.build_for_zone(zone_id, self.config)
        previous = await self.repository.latest_for_zone(zone_id)
        return self._build_assessment(facts, previous.score if previous else None)

    async def assess_plant(self) -> PlantRiskSummary:
        facts_by_zone = await self.facts_builder.build_for_plant(self.config)
        assessments = []
        for facts in facts_by_zone.values():
            previous = await self.repository.latest_for_zone(facts.zone_id)
            assessments.append(self._build_assessment(facts, previous.score if previous else None))
        assessments.sort(key=lambda a: a.zone_name)

        highest = max(assessments, key=lambda a: a.score, default=None)
        return PlantRiskSummary(
            generated_at=datetime.now(timezone.utc),
            zones=assessments,
            highest_risk_zone_id=highest.zone_id if highest else None,
            plant_wide_emergency_active=any(a.is_emergency_override for a in assessments),
        )

    async def evaluate(self, facts: ZoneFacts) -> tuple[RiskAssessment, RiskSnapshot | None]:
        """Used by RiskScheduler. Computes the assessment, compares it against the last
        persisted snapshot for this zone, and only writes a new row on a meaningful change
        (level changed, or score moved by more than SCORE_DELTA_PERSIST_THRESHOLD). Returns the
        assessment unconditionally (the Recommendation Engine reconciles against it every tick,
        independent of whether this particular tick was persist-worthy) alongside the snapshot,
        which is None on ticks that didn't warrant a new row."""
        previous = await self.repository.latest_for_zone(facts.zone_id)
        assessment = self._build_assessment(facts, previous.score if previous else None)

        if not self._should_persist(previous, assessment):
            return assessment, None

        snapshot = await self.repository.create(
            {
                "zone_id": facts.zone_id,
                "score": assessment.score,
                "level": assessment.level.value,
                "confidence": assessment.confidence_score,
                "is_emergency_override": assessment.is_emergency_override,
                "categories": [c.model_dump(mode="json") for c in assessment.categories],
                "contributors": [c.model_dump(mode="json") for c in assessment.contributors],
                "explanation": assessment.explanation,
                "engine_version": assessment.engine_version,
                "trigger_source": TRIGGER_SOURCE_SCHEDULER,
                "evaluation_duration_ms": assessment.evaluation_duration_ms,
                "evaluated_at": assessment.evaluated_at,
            }
        )
        if previous is None:
            # A zone's very first snapshot is always persisted (per _should_persist), but with
            # no prior row there's no "transition" to compare against. If it's already elevated,
            # that's still a fact the Operational Timeline needs — a zone seeded already
            # critical must not read as silently normal for having no risk_level event at all.
            if snapshot.level != RiskLevel.NORMAL.value:
                await self._emit_initial_level_event(snapshot, facts.zone_name)
        elif previous.level != snapshot.level:
            await self._emit_level_change_event(previous, snapshot, facts.zone_name)
        return assessment, snapshot

    async def _emit_initial_level_event(self, snapshot: RiskSnapshot, zone_name: str) -> None:
        await self.event_repository.create(
            {
                "zone_id": snapshot.zone_id,
                "risk_snapshot_id": snapshot.id,
                "event_type": EventType.RISK_LEVEL_INCREASED.value,
                "title": f"{zone_name} risk level observed at {snapshot.level.upper()} (first assessment)",
                "description": None,
                "occurred_at": snapshot.evaluated_at,
            }
        )

    async def _emit_level_change_event(
        self, previous: RiskSnapshot, snapshot: RiskSnapshot, zone_name: str
    ) -> None:
        """Only fires on an actual level transition (never on a same-level score wobble, even
        though that can also trigger persistence) — matches the Operational Timeline's noise
        principle of logging state transitions, not every score movement."""
        increased = _RISK_LEVEL_RANK[snapshot.level] > _RISK_LEVEL_RANK[previous.level]
        event_type = EventType.RISK_LEVEL_INCREASED if increased else EventType.RISK_LEVEL_DECREASED
        direction = "increased" if increased else "decreased"
        await self.event_repository.create(
            {
                "zone_id": snapshot.zone_id,
                "risk_snapshot_id": snapshot.id,
                "event_type": event_type.value,
                "title": f"{zone_name} risk level {direction}: {previous.level.upper()} → {snapshot.level.upper()}",
                "description": None,
                "occurred_at": snapshot.evaluated_at,
            }
        )

    async def evaluate_and_persist_if_changed(self, facts: ZoneFacts) -> RiskSnapshot | None:
        _, snapshot = await self.evaluate(facts)
        return snapshot

    async def history_for_zone(
        self,
        zone_id: UUID,
        *,
        since: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[RiskSnapshotRead], int]:
        items, total = await self.repository.history_for_zone(
            zone_id, since=since, page=page, page_size=page_size
        )
        return [await self._to_snapshot_read(s) for s in items], total

    async def recent_level_changes(self, *, limit: int = 50) -> list[RiskSnapshotRead]:
        snapshots = await self.repository.recent_changes(limit=limit)
        return [await self._to_snapshot_read(s) for s in snapshots]

    def _should_persist(self, previous: RiskSnapshot | None, assessment: RiskAssessment) -> bool:
        if previous is None:
            return True
        return (
            previous.level != assessment.level.value
            or abs(previous.score - assessment.score) > SCORE_DELTA_PERSIST_THRESHOLD
        )

    def _build_assessment(self, facts: ZoneFacts, previous_score: int | None) -> RiskAssessment:
        start = time.perf_counter()
        results: list[RuleResult] = [rule.evaluate(facts, self.config) for rule in ALL_RULES]
        agg = aggregate(results, self.config)
        category_breakdown = build_category_breakdown(results, self.config)
        confidence_score = compute_confidence(facts, agg.triggered, self.config)
        confidence_label = confidence_label_for(confidence_score, self.config)
        explanation = generate_explanation(
            facts.zone_name,
            agg.level,
            agg.score,
            agg.triggered,
            agg.is_emergency_override,
            self.config.explanation_top_n,
        )
        score_delta, trend_direction = compute_trend(agg.score, previous_score)
        duration_ms = int((time.perf_counter() - start) * 1000)

        return RiskAssessment(
            zone_id=facts.zone_id,
            zone_name=facts.zone_name,
            engine_version=ENGINE_VERSION,
            score=agg.score,
            level=agg.level,
            is_emergency_override=agg.is_emergency_override,
            confidence_score=confidence_score,
            confidence_label=confidence_label,
            categories=[
                CategoryRisk(category=c.category, score=c.score, level=c.level, top_contributor=c.top_contributor)
                for c in category_breakdown
            ],
            contributors=[self._to_contributor(r) for r in agg.triggered],
            recommended_actions=self._build_recommended_actions(agg.triggered),
            previous_score=previous_score,
            score_delta=score_delta,
            trend_direction=trend_direction,
            evaluation_duration_ms=duration_ms,
            explanation=explanation,
            evaluated_at=facts.evaluated_at,
        )

    def _build_recommended_actions(self, triggered: list[RuleResult]) -> list[RecommendedAction]:
        ranked = sorted((r for r in triggered if r.suggested_action), key=lambda r: -r.impact)
        seen: set[str] = set()
        actions: list[RecommendedAction] = []
        for r in ranked:
            if r.suggested_action in seen:
                continue
            seen.add(r.suggested_action)
            actions.append(RecommendedAction(rule_id=r.rule_id, action=r.suggested_action, priority=r.severity))
            if len(actions) >= self.config.recommended_actions_limit:
                break
        return actions

    def _to_contributor(self, result: RuleResult) -> RiskContributor:
        return RiskContributor(
            rule_id=result.rule_id,
            category=result.category,
            factor=result.factor,
            impact=result.impact,
            severity=result.severity,
            rationale=result.rationale,
            source_refs=[
                EntityRefRead(entity_type=e.entity_type, entity_id=e.entity_id, label=e.label)
                for e in result.referenced_entities
            ],
        )

    async def _to_snapshot_read(self, snapshot: RiskSnapshot) -> RiskSnapshotRead:
        previous = await self.repository.previous_before(snapshot.zone_id, snapshot.evaluated_at)
        previous_score = previous.score if previous else None
        score_delta, trend_direction = compute_trend(snapshot.score, previous_score)

        return RiskSnapshotRead(
            id=snapshot.id,
            created_at=snapshot.created_at,
            updated_at=snapshot.updated_at,
            zone_id=snapshot.zone_id,
            score=snapshot.score,
            level=RiskLevel(snapshot.level),
            confidence_score=snapshot.confidence,
            confidence_label=confidence_label_for(snapshot.confidence, self.config),
            is_emergency_override=snapshot.is_emergency_override,
            categories=[CategoryRisk(**c) for c in snapshot.categories],
            contributors=[RiskContributor(**c) for c in snapshot.contributors],
            explanation=snapshot.explanation,
            engine_version=snapshot.engine_version,
            trigger_source=snapshot.trigger_source,
            evaluation_duration_ms=snapshot.evaluation_duration_ms,
            evaluated_at=snapshot.evaluated_at,
            previous_score=previous_score,
            score_delta=score_delta,
            trend_direction=trend_direction,
        )
