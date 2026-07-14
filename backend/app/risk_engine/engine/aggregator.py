"""Score aggregation: clamped additive sum of triggered rule impacts, plus a separate
emergency-override post-step. Kept as two distinct steps (not folded into the additive sum) so
every point of score always traces to a specific rule, and an emergency override never
silently manufactures score out of nowhere.
"""

from dataclasses import dataclass

from app.risk_engine.config.schema import RiskCategory, RiskEngineConfig, RiskLevel, SeverityBandsConfig
from app.risk_engine.rules.base import RuleResult


@dataclass(frozen=True)
class AggregationResult:
    score: int
    level: RiskLevel
    triggered: list[RuleResult]
    is_emergency_override: bool


@dataclass(frozen=True)
class CategoryBreakdown:
    category: RiskCategory
    score: int
    level: RiskLevel
    top_contributor: str | None  # the `factor` of the highest-impact triggered rule in this category, or None if none triggered


def _level_for_score(score: int, bands: SeverityBandsConfig) -> RiskLevel:
    if score >= bands.high_max:
        return RiskLevel.CRITICAL
    if score >= bands.moderate_max:
        return RiskLevel.HIGH
    if score >= bands.low_max:
        return RiskLevel.MODERATE
    if score >= bands.normal_max:
        return RiskLevel.LOW
    return RiskLevel.NORMAL


def aggregate(results: list[RuleResult], config: RiskEngineConfig) -> AggregationResult:
    """Clamped sum of triggered rules' impact to [0,100]. Separate emergency-override
    post-step: if ANY triggered result has is_emergency_override=True, force level=CRITICAL
    and floor the score at config.severity_bands.emergency_score_floor (never lowers a higher
    score)."""
    triggered = [r for r in results if r.triggered]
    score = max(0, min(100, sum(r.impact for r in triggered)))
    level = _level_for_score(score, config.severity_bands)

    is_emergency_override = any(r.is_emergency_override for r in triggered)
    if is_emergency_override:
        score = max(score, config.severity_bands.emergency_score_floor)
        level = RiskLevel.CRITICAL

    return AggregationResult(
        score=score,
        level=level,
        triggered=triggered,
        is_emergency_override=is_emergency_override,
    )


def build_category_breakdown(results: list[RuleResult], config: RiskEngineConfig) -> list[CategoryBreakdown]:
    """Calls aggregate() once per RiskCategory (in enum declaration order) on the subset of
    `results` belonging to that category. Always returns exactly 7 entries, even for
    categories with zero triggered rules (score=0, level=NORMAL, top_contributor=None)."""
    breakdown: list[CategoryBreakdown] = []
    for category in RiskCategory:
        category_results = [r for r in results if r.category == category]
        category_aggregation = aggregate(category_results, config)

        top_contributor: str | None = None
        if category_aggregation.triggered:
            top_contributor = max(category_aggregation.triggered, key=lambda r: r.impact).factor

        breakdown.append(
            CategoryBreakdown(
                category=category,
                score=category_aggregation.score,
                level=category_aggregation.level,
                top_contributor=top_contributor,
            )
        )
    return breakdown
