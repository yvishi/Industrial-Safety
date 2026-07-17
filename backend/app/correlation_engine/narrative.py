"""
Deterministic narrative generation for Incidents — NOT AI/NLP generation, same posture as
risk_engine/engine/explain.py: every clause traces back to a structured fact already computed
elsewhere (top risk contributor's rationale, top recommendation's title, timestamps). A fixed
three-slot structure — trigger clause / response clause / outcome clause — not open-ended
composition, per the architecture review's explicit "keep the template count small" decision.
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from app.risk_engine.config.schema import RiskLevel


@dataclass(frozen=True)
class NarrativeInput:
    zone_name: str
    classification: str
    risk_severity_at_open: RiskLevel | None
    status: str  # open | resolved | closed
    opened_at: datetime
    resolved_at: datetime | None
    top_contributor_rationale: str | None = None
    top_recommendation_title: str | None = None
    recommendation_acknowledged: bool = False


def generate_title(narrative_input: NarrativeInput) -> str:
    classification_label = narrative_input.classification.replace("_", " ").title()
    if narrative_input.risk_severity_at_open is None:
        return f"{narrative_input.zone_name} — {classification_label}"
    return (
        f"{narrative_input.zone_name} — {classification_label} "
        f"({narrative_input.risk_severity_at_open.value.upper()})"
    )


def generate_summary(narrative_input: NarrativeInput) -> str:
    trigger = _trigger_clause(narrative_input)
    response = _response_clause(narrative_input)
    outcome = _outcome_clause(narrative_input)
    return f"{trigger}{response}{outcome}"


def _trigger_clause(narrative_input: NarrativeInput) -> str:
    if narrative_input.top_contributor_rationale:
        return narrative_input.top_contributor_rationale.rstrip(".") + "."
    if narrative_input.risk_severity_at_open is not None:
        return f"{narrative_input.zone_name} risk reached {narrative_input.risk_severity_at_open.value.upper()}."
    return f"Manually declared for {narrative_input.zone_name}."


def _response_clause(narrative_input: NarrativeInput) -> str:
    if not narrative_input.top_recommendation_title:
        return ""
    if narrative_input.recommendation_acknowledged:
        return f" {narrative_input.top_recommendation_title} was recommended and acknowledged."
    return f" {narrative_input.top_recommendation_title} was recommended; awaiting acknowledgement."


def _as_aware_utc(value: datetime) -> datetime:
    """SQLite (used in tests) doesn't reliably round-trip tz-aware datetimes even through a
    DateTime(timezone=True) column, unlike Postgres — treat a naive value as UTC rather than
    let a resolved_at/opened_at subtraction crash on mixed aware/naive datetimes."""
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def _outcome_clause(narrative_input: NarrativeInput) -> str:
    if narrative_input.status not in ("resolved", "closed"):
        return " Still active."
    if narrative_input.resolved_at is None:
        return " Conditions returned to normal."
    duration = _as_aware_utc(narrative_input.resolved_at) - _as_aware_utc(narrative_input.opened_at)
    minutes = max(1, int(duration.total_seconds() // 60))
    unit = "minute" if minutes == 1 else "minutes"
    return f" Conditions returned to normal after {minutes} {unit}."
