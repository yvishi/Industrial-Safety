"""Deterministic template combiner that turns triggered rules into a human-readable
explanation sentence — NOT NLP generation. Every word traces back to a rule's rationale.
"""

from app.risk_engine.config.schema import RiskLevel
from app.risk_engine.rules.base import RuleResult

_EMERGENCY_PREFIX = "EMERGENCY CONDITION ACTIVE. "


def generate_explanation(
    zone_name: str,
    level: RiskLevel,
    score: int,
    triggered: list[RuleResult],
    is_emergency_override: bool,
    top_n: int,
) -> str:
    if not triggered:
        return f"{zone_name} shows no elevated risk factors; all monitored conditions are within normal parameters."

    sorted_triggered = sorted(triggered, key=lambda r: (-r.impact, r.rule_id))
    top = sorted_triggered[:top_n]

    lead = f"{zone_name} is at {level.value.upper()} risk (score {score}/100)."
    factors = "; ".join(r.rationale.rstrip(".") for r in top) + "."
    body = f"{lead} Primary factors: {factors}"

    remaining = len(sorted_triggered) - top_n
    if remaining > 0:
        body += f" ({remaining} additional factor(s) also contributing.)"

    if is_emergency_override:
        body = _EMERGENCY_PREFIX + body

    return body
