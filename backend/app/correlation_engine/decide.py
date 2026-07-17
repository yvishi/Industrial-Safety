"""
Pure decision logic for the Correlation Engine: given a zone's current RiskAssessment, the
Recommendation Engine's already-reconciled active set for that zone (summarized down to just
the highest active priority — decide() never needs the full rows), whichever Incident is
currently OPEN for that zone (if any), and the debounce counters carried over from the previous
tick, decide what should happen to that Incident this tick.

No I/O, no DB session, no ORM objects — mirrors risk_engine's rules and
recommendation_engine/generator.py's own "pure function over a plain input shape" boundary.
IncidentService owns persistence and the per-zone ThresholdState it feeds in/out of decide().

Recurrence deliberately always opens a NEW Incident rather than "reopening" an old
resolved-but-not-closed one — mirroring the Recommendation Engine's own fix for the identical
problem (a resolved row can legitimately recur; the fix there was a fresh row per recurrence,
scoped by a partial-unique-index on non-resolved rows, never reusing the old one). An earlier
draft of this module had a "reopen" action that resurrected the most recent resolved-not-closed
incident for the zone; that turned out to conflate causally-unrelated episodes (e.g. an
unrelated equipment fault hours later would "reopen" an old, already-resolved gas-hazard
incident) and corrupt its opened_at-based duration narrative. Resolved-not-closed incidents
simply sit there awaiting an operator's close() — recurrence, related or not, always gets its
own new Incident row.
"""

from dataclasses import dataclass

from app.risk_engine.config.schema import RiskLevel
from app.schemas.recommendation import RecommendationPriority

from .config import DEFAULT_CORRELATION_CONFIG, CorrelationEngineConfig

_RISK_LEVEL_RANK: dict[RiskLevel, int] = {level: i for i, level in enumerate(RiskLevel)}
_PRIORITY_RANK: dict[RecommendationPriority, int] = {
    RecommendationPriority.LOW: 0,
    RecommendationPriority.MODERATE: 1,
    RecommendationPriority.HIGH: 2,
    RecommendationPriority.CRITICAL: 3,
}


@dataclass(frozen=True)
class ThresholdState:
    """Per-zone debounce counters, carried across ticks by whichever caller owns the incident
    lifecycle for this zone (see RiskScheduler — it, not IncidentService, is the long-lived
    object across ticks, so it owns this dict)."""

    consecutive_ticks_above: int = 0
    consecutive_ticks_below: int = 0


@dataclass(frozen=True)
class OpenIncidentSnapshot:
    """The minimal shape decide() needs from the zone's currently-OPEN Incident row, if any —
    never the full ORM object, so this module stays a pure function over plain data. Presence of
    an instance always means "open"; resolved/closed incidents are never passed in."""

    peak_risk_severity: RiskLevel


@dataclass(frozen=True)
class IncidentDecision:
    action: str  # "open" | "keep_open" | "resolve" | "none"
    peak_risk_severity: RiskLevel | None = None


def _qualifies(
    level: RiskLevel,
    is_emergency_override: bool,
    highest_active_priority: RecommendationPriority | None,
    config: CorrelationEngineConfig,
) -> bool:
    if is_emergency_override:
        return True
    if _RISK_LEVEL_RANK[level] >= _RISK_LEVEL_RANK[config.open_trigger_level]:
        return True
    if highest_active_priority is not None and (
        _PRIORITY_RANK[highest_active_priority] >= _PRIORITY_RANK[config.open_trigger_recommendation_priority]
    ):
        return True
    return False


def decide(
    *,
    level: RiskLevel,
    is_emergency_override: bool,
    highest_active_priority: RecommendationPriority | None,
    current_incident: OpenIncidentSnapshot | None,
    previous_state: ThresholdState,
    config: CorrelationEngineConfig = DEFAULT_CORRELATION_CONFIG,
) -> tuple[ThresholdState, IncidentDecision]:
    qualifies = _qualifies(level, is_emergency_override, highest_active_priority, config)

    new_state = (
        ThresholdState(consecutive_ticks_above=previous_state.consecutive_ticks_above + 1, consecutive_ticks_below=0)
        if qualifies
        else ThresholdState(consecutive_ticks_above=0, consecutive_ticks_below=previous_state.consecutive_ticks_below + 1)
    )

    if current_incident is None:
        should_open = is_emergency_override or (
            qualifies and new_state.consecutive_ticks_above >= config.min_ticks_to_open
        )
        if not should_open:
            return new_state, IncidentDecision(action="none")
        return new_state, IncidentDecision(action="open", peak_risk_severity=level)

    # An incident is currently open for this zone.
    if qualifies:
        worse = _RISK_LEVEL_RANK[level] > _RISK_LEVEL_RANK[current_incident.peak_risk_severity]
        new_peak = level if worse else current_incident.peak_risk_severity
        return new_state, IncidentDecision(action="keep_open", peak_risk_severity=new_peak)

    if new_state.consecutive_ticks_below >= config.min_ticks_to_resolve:
        return new_state, IncidentDecision(action="resolve")

    return new_state, IncidentDecision(action="keep_open", peak_risk_severity=current_incident.peak_risk_severity)
