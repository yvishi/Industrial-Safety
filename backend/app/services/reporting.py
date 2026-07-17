"""
Reports & Analytics: read-only cross-entity aggregation over Incident/RiskSnapshot/
Recommendation/Zone. Bespoke aggregator, not a BaseService[Model] CRUD subclass — same
justification as RiskService (see services/risk.py's class docstring): a report has no
single-entity CRUD lifecycle, nothing here is ever created/updated/deleted, so a repository
layer would only add indirection around plain SQLAlchemy selects. Queries directly via the
AsyncSession, exactly like RiskService's "no owning table" posture recommends.

Every method pulls the relevant rows for the whole [since, until] window in a small, fixed
number of queries and does the aggregation (bucketing, grouping, averaging) in Python — never
one query per bucket/zone/rule. This mirrors RiskService.assess_plant's per-zone loop being
capped by "how many zones exist", not by report complexity, and is called out explicitly by
the spec this module was built against: the datasets here are small (a plant's incidents/
snapshots/recommendations), so Python-side aggregation keeps behavior identical across the
Postgres/SQLite dual-dialect test setup without hand-writing dialect-specific date-trunc SQL.
"""

import bisect
from collections import Counter
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident import Incident
from app.models.recommendation import Recommendation
from app.models.risk_snapshot import RiskSnapshot
from app.models.zone import Zone
from app.risk_engine.config.schema import RiskCategory, RiskLevel, TrendDirection
from app.schemas.incident import IncidentClassification
from app.schemas.reports import (
    ClassificationCount,
    HazardCategoryFrequency,
    IncidentResponseReport,
    RecommendationTemplateFrequency,
    SafetyTrendPeriodPoint,
    SafetyTrendReport,
    TriggeredRuleFrequency,
    ZoneHazardReport,
    ZoneHazardSummary,
)
from app.services.risk import build_rule_catalog

DEFAULT_WINDOW = timedelta(days=30)
# Bucket-length thresholds, in whole days of the [since, until] window.
_DAILY_WINDOW_MAX = timedelta(days=14)
_WEEKLY_WINDOW_MAX = timedelta(days=120)
# Percent-change-in-incidents-opened cutoffs for the safety-trend headline direction.
_TREND_DOWN_THRESHOLD = -0.15
_TREND_UP_THRESHOLD = 0.15

_OPEN = "open"
_REPORTABLE = IncidentClassification.REPORTABLE_INCIDENT.value


def _as_aware_utc(value: datetime) -> datetime:
    """SQLite (tests) round-trips DateTime(timezone=True) columns naive; they were stored as
    UTC — same normalization as risk_engine/facts_builder.py's _as_aware_utc, needed here
    because bucketing/averaging compares these against tz-aware since/until/now values."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _default_window(since: datetime | None, until: datetime | None) -> tuple[datetime, datetime]:
    resolved_until = until if until is not None else datetime.now(timezone.utc)
    resolved_since = since if since is not None else resolved_until - DEFAULT_WINDOW
    return _as_aware_utc(resolved_since), _as_aware_utc(resolved_until)


def _add_month(dt: datetime) -> datetime:
    if dt.month == 12:
        return dt.replace(year=dt.year + 1, month=1)
    return dt.replace(month=dt.month + 1)


def _build_periods(since: datetime, until: datetime, granularity: str) -> list[tuple[datetime, datetime]]:
    """Every bucket in [since, until], including trailing zero-activity ones — a supervisor
    needs to see the flat/quiet weeks too, not just ones that had rows."""
    if granularity == "day":
        start = since.replace(hour=0, minute=0, second=0, microsecond=0)
        step = timedelta(days=1)
        advance = lambda d: d + step  # noqa: E731
    elif granularity == "week":
        monday = since - timedelta(days=since.weekday())
        start = monday.replace(hour=0, minute=0, second=0, microsecond=0)
        step = timedelta(days=7)
        advance = lambda d: d + step  # noqa: E731
    else:
        start = since.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        advance = _add_month

    periods: list[tuple[datetime, datetime]] = []
    while start < until:
        end = advance(start)
        periods.append((start, end))
        start = end
    return periods


def _granularity_for(since: datetime, until: datetime) -> str:
    window = until - since
    if window <= _DAILY_WINDOW_MAX:
        return "day"
    if window <= _WEEKLY_WINDOW_MAX:
        return "week"
    return "month"


def _bucket_index(period_starts: list[datetime], ts: datetime) -> int | None:
    idx = bisect.bisect_right(period_starts, ts) - 1
    if 0 <= idx < len(period_starts):
        return idx
    return None


def _top_category(counter: Counter) -> RiskCategory | None:
    """First category (in RiskCategory's declared order) with the highest occurrence count.
    A stable, deterministic tie-break beats an arbitrary dict/Counter insertion order."""
    best_cat: RiskCategory | None = None
    best_count = 0
    for cat in RiskCategory:
        count = counter.get(cat.value, 0)
        if count > best_count:
            best_count = count
            best_cat = cat
    return best_cat


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


class ReportingService:
    """Read-only aggregator behind GET /api/v1/reports/*. See module docstring."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def safety_trend(
        self,
        since: datetime | None = None,
        until: datetime | None = None,
        zone_id: UUID | None = None,
    ) -> SafetyTrendReport:
        since, until = _default_window(since, until)
        granularity = _granularity_for(since, until)
        periods = _build_periods(since, until, granularity)
        period_starts = [p[0] for p in periods]

        opened_counts = [0] * len(periods)
        resolved_counts = [0] * len(periods)
        level_counts = [dict.fromkeys((level.value for level in RiskLevel), 0) for _ in periods]

        incident_stmt = select(Incident).where(Incident.opened_at >= since, Incident.opened_at <= until)
        if zone_id is not None:
            incident_stmt = incident_stmt.where(Incident.primary_zone_id == zone_id)
        # resolved_at can fall in-window even when opened_at didn't (an incident opened before
        # `since` but resolved during it) — a separate query on resolved_at keeps that case correct.
        resolved_stmt = select(Incident).where(Incident.resolved_at >= since, Incident.resolved_at <= until)
        if zone_id is not None:
            resolved_stmt = resolved_stmt.where(Incident.primary_zone_id == zone_id)

        opened_incidents = list((await self.session.execute(incident_stmt)).scalars().all())
        resolved_incidents = list((await self.session.execute(resolved_stmt)).scalars().all())

        for incident in opened_incidents:
            idx = _bucket_index(period_starts, _as_aware_utc(incident.opened_at))
            if idx is not None:
                opened_counts[idx] += 1
        for incident in resolved_incidents:
            idx = _bucket_index(period_starts, _as_aware_utc(incident.resolved_at))
            if idx is not None:
                resolved_counts[idx] += 1

        snapshot_stmt = select(RiskSnapshot).where(
            RiskSnapshot.evaluated_at >= since, RiskSnapshot.evaluated_at <= until
        )
        if zone_id is not None:
            snapshot_stmt = snapshot_stmt.where(RiskSnapshot.zone_id == zone_id)
        snapshots = list((await self.session.execute(snapshot_stmt)).scalars().all())
        for snapshot in snapshots:
            idx = _bucket_index(period_starts, _as_aware_utc(snapshot.evaluated_at))
            if idx is not None:
                level_counts[idx][snapshot.level] += 1

        points = [
            SafetyTrendPeriodPoint(
                period_start=period_starts[i],
                incidents_opened=opened_counts[i],
                incidents_resolved=resolved_counts[i],
                normal_count=level_counts[i][RiskLevel.NORMAL.value],
                low_count=level_counts[i][RiskLevel.LOW.value],
                moderate_count=level_counts[i][RiskLevel.MODERATE.value],
                high_count=level_counts[i][RiskLevel.HIGH.value],
                critical_count=level_counts[i][RiskLevel.CRITICAL.value],
            )
            for i in range(len(periods))
        ]

        midpoint = since + (until - since) / 2
        first_half = sum(1 for i in opened_incidents if since <= _as_aware_utc(i.opened_at) < midpoint)
        second_half = sum(1 for i in opened_incidents if midpoint <= _as_aware_utc(i.opened_at) <= until)
        trend_direction, trend_summary = self._trend(first_half, second_half)

        return SafetyTrendReport(
            since=since,
            until=until,
            zone_id=zone_id,
            period_granularity=granularity,
            periods=points,
            total_incidents_opened=len(opened_incidents),
            total_incidents_resolved=len(resolved_incidents),
            trend_direction=trend_direction,
            trend_summary=trend_summary,
        )

    def _trend(self, first_half: int, second_half: int) -> tuple[TrendDirection, str]:
        if first_half == 0 and second_half == 0:
            return TrendDirection.FLAT, "No incidents were opened during this period."

        pct_change = (second_half - first_half) / max(first_half, 1)
        if pct_change <= _TREND_DOWN_THRESHOLD:
            return (
                TrendDirection.DOWN,
                f"Incidents opened fell from {first_half} to {second_half} across this period.",
            )
        if pct_change >= _TREND_UP_THRESHOLD:
            return (
                TrendDirection.UP,
                f"Incidents opened rose from {first_half} to {second_half} across this period.",
            )
        return TrendDirection.FLAT, "No meaningful change in incident volume across this period."

    async def zone_hazard_analysis(
        self,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> ZoneHazardReport:
        since, until = _default_window(since, until)

        zones = list((await self.session.execute(select(Zone))).scalars().all())

        incident_stmt = select(Incident).where(Incident.opened_at >= since, Incident.opened_at <= until)
        incidents = list((await self.session.execute(incident_stmt)).scalars().all())
        incidents_by_zone: dict[UUID, list[Incident]] = {}
        for incident in incidents:
            incidents_by_zone.setdefault(incident.primary_zone_id, []).append(incident)

        snapshot_stmt = select(RiskSnapshot).where(
            RiskSnapshot.evaluated_at >= since, RiskSnapshot.evaluated_at <= until
        )
        snapshots = list((await self.session.execute(snapshot_stmt)).scalars().all())
        snapshots_by_zone: dict[UUID, list[RiskSnapshot]] = {}
        for snapshot in snapshots:
            snapshots_by_zone.setdefault(snapshot.zone_id, []).append(snapshot)

        zone_summaries: list[ZoneHazardSummary] = []
        for zone in zones:
            zone_incidents = incidents_by_zone.get(zone.id, [])
            zone_snapshots = snapshots_by_zone.get(zone.id, [])

            scores = [s.score for s in zone_snapshots]
            category_counter: Counter = Counter()
            for snapshot in zone_snapshots:
                for contributor in snapshot.contributors:
                    category_counter[contributor["category"]] += 1

            zone_summaries.append(
                ZoneHazardSummary(
                    zone_id=zone.id,
                    zone_name=zone.name,
                    incident_count=len(zone_incidents),
                    # Time-boxed to stay consistent with the rest of this report: incidents
                    # OPENED within [since, until] that are still open, not every open incident
                    # regardless of when it opened.
                    open_incident_count=sum(1 for i in zone_incidents if i.status == _OPEN),
                    reportable_incident_count=sum(
                        1 for i in zone_incidents if i.classification == _REPORTABLE
                    ),
                    avg_risk_score=_mean(scores),
                    top_category=_top_category(category_counter),
                )
            )

        zone_summaries.sort(key=lambda z: (-z.incident_count, z.zone_name))

        # Plant-wide: what actually fired, not what could have — zero-trigger categories/rules
        # are noise here (unlike the per-zone list above, where a quiet zone is a fact worth
        # showing).
        plant_category_counter: Counter = Counter()
        plant_rule_counter: Counter = Counter()
        for snapshot in snapshots:
            for contributor in snapshot.contributors:
                plant_category_counter[contributor["category"]] += 1
                plant_rule_counter[contributor["rule_id"]] += 1

        hazard_categories = [
            HazardCategoryFrequency(category=RiskCategory(category), trigger_count=count)
            for category, count in plant_category_counter.most_common()
        ]

        rule_catalog = {entry.rule_id: entry for entry in build_rule_catalog()}
        top_rules: list[TriggeredRuleFrequency] = []
        for rule_id, count in plant_rule_counter.most_common():
            entry = rule_catalog.get(rule_id)
            if entry is None:
                # Should not happen in practice (every triggered rule_id comes from ALL_RULES),
                # but a report must never 500 over a stale/unknown rule_id in old data.
                continue
            top_rules.append(
                TriggeredRuleFrequency(
                    rule_id=rule_id,
                    category=entry.category,
                    description=entry.description,
                    trigger_count=count,
                )
            )
            if len(top_rules) >= 10:
                break

        return ZoneHazardReport(
            since=since,
            until=until,
            zones=zone_summaries,
            hazard_categories=hazard_categories,
            top_rules=top_rules,
        )

    async def incident_response(
        self,
        since: datetime | None = None,
        until: datetime | None = None,
        zone_id: UUID | None = None,
    ) -> IncidentResponseReport:
        since, until = _default_window(since, until)

        opened_stmt = select(Incident).where(Incident.opened_at >= since, Incident.opened_at <= until)
        if zone_id is not None:
            opened_stmt = opened_stmt.where(Incident.primary_zone_id == zone_id)
        opened_incidents = list((await self.session.execute(opened_stmt)).scalars().all())

        resolved_stmt = select(Incident).where(Incident.resolved_at >= since, Incident.resolved_at <= until)
        if zone_id is not None:
            resolved_stmt = resolved_stmt.where(Incident.primary_zone_id == zone_id)
        resolved_incidents = list((await self.session.execute(resolved_stmt)).scalars().all())

        closed_stmt = select(Incident).where(Incident.closed_at >= since, Incident.closed_at <= until)
        if zone_id is not None:
            closed_stmt = closed_stmt.where(Incident.primary_zone_id == zone_id)
        closed_incidents = list((await self.session.execute(closed_stmt)).scalars().all())

        recommendation_stmt = select(Recommendation).where(
            Recommendation.acknowledged_at >= since, Recommendation.acknowledged_at <= until
        )
        if zone_id is not None:
            recommendation_stmt = recommendation_stmt.where(Recommendation.zone_id == zone_id)
        acknowledged_recommendations = list((await self.session.execute(recommendation_stmt)).scalars().all())

        generated_stmt = select(Recommendation).where(
            Recommendation.first_generated_at >= since, Recommendation.first_generated_at <= until
        )
        if zone_id is not None:
            generated_stmt = generated_stmt.where(Recommendation.zone_id == zone_id)
        generated_recommendations = list((await self.session.execute(generated_stmt)).scalars().all())

        resolve_hours = [
            (_as_aware_utc(i.resolved_at) - _as_aware_utc(i.opened_at)).total_seconds() / 3600
            for i in resolved_incidents
        ]
        close_hours = [
            (_as_aware_utc(i.closed_at) - _as_aware_utc(i.opened_at)).total_seconds() / 3600
            for i in closed_incidents
        ]
        acknowledge_minutes = [
            (_as_aware_utc(r.acknowledged_at) - _as_aware_utc(r.first_generated_at)).total_seconds() / 60
            for r in acknowledged_recommendations
        ]

        classification_counter = Counter(i.classification for i in opened_incidents)
        classification_breakdown = [
            ClassificationCount(classification=c, count=classification_counter.get(c.value, 0))
            for c in IncidentClassification
        ]

        template_counter = Counter(r.template_id for r in generated_recommendations)
        template_info: dict[str, tuple[str, str]] = {}
        for r in generated_recommendations:
            template_info.setdefault(r.template_id, (r.title, r.category))
        top_recommendation_templates = [
            RecommendationTemplateFrequency(
                template_id=template_id,
                title=template_info[template_id][0],
                category=template_info[template_id][1],
                trigger_count=count,
            )
            for template_id, count in template_counter.most_common(10)
        ]

        return IncidentResponseReport(
            since=since,
            until=until,
            zone_id=zone_id,
            incidents_resolved_count=len(resolved_incidents),
            incidents_closed_count=len(closed_incidents),
            mean_time_to_resolve_hours=_mean(resolve_hours),
            mean_time_to_close_hours=_mean(close_hours),
            recommendations_acknowledged_count=len(acknowledged_recommendations),
            mean_time_to_acknowledge_minutes=_mean(acknowledge_minutes),
            classification_breakdown=classification_breakdown,
            top_recommendation_templates=top_recommendation_templates,
        )
