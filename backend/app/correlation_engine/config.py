"""
Correlation Engine configuration: the thresholds that decide when a zone's condition is
significant enough to open an Incident, and how much debounce to apply before opening or
auto-resolving one. Config-as-code, plain Pydantic, no DB — mirrors
risk_engine/config/schema.py's own "a domain expert retunes this by editing Python" precedent.

Why debounce lives here at all: CRE's live RiskAssessment.level is NOT itself debounced (only
its *persistence* is change-gated — see RiskService._should_persist), so a score sitting near a
level boundary can flicker tick-to-tick without ever failing to persist a "changed" snapshot.
Reacting to that raw live value every tick would open/resolve/reopen an Incident every ~15s at
a boundary — an alert-fatigue and safety-credibility problem in a real control room. This is new
hysteresis logic this codebase doesn't have anywhere else (Recommendation doesn't need it — its
candidates come from discrete rule triggers, not a continuous score near a floating boundary).
"""

from pydantic import BaseModel

from app.risk_engine.config.schema import RiskLevel
from app.schemas.recommendation import RecommendationPriority


class CorrelationEngineConfig(BaseModel):
    # A zone auto-opens an Incident once its live RiskAssessment.level reaches this level or
    # above, sustained for min_ticks_to_open consecutive ticks — or immediately, regardless of
    # the counter, if assessment.is_emergency_override is set (it's already a discrete boolean
    # CRE computes without going through any score-delta gate, so it doesn't need — and
    # shouldn't get — boundary hysteresis of its own).
    open_trigger_level: RiskLevel = RiskLevel.HIGH
    # ...or once the zone has any Recommendation at this priority or above, independent of the
    # counter below — Recommendation's own reconcile-driven lifecycle is already the stability
    # mechanism for *that* signal, so no additional debounce is applied on top of it here.
    open_trigger_recommendation_priority: RecommendationPriority = RecommendationPriority.CRITICAL
    min_ticks_to_open: int = 2
    # Deliberately the same length as min_ticks_to_open in v1 — an asymmetric (slower-to-clear)
    # debounce is a plausible future tuning, not needed yet.
    min_ticks_to_resolve: int = 2


DEFAULT_CORRELATION_CONFIG = CorrelationEngineConfig()
