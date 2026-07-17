"""Pure unit tests for the Correlation Engine's decision logic and narrative generation — no
DB, hand-built fixtures, mirroring test_risk_engine.py / test_recommendation_engine.py's style.

The debounce/hysteresis tests here are the regression coverage for the specific safety concern
raised in architecture review: CRE's live RiskAssessment.level is NOT itself debounced (only its
*persistence* is change-gated), so without the ThresholdState counters in decide(), a score
oscillating across a level boundary would open/resolve/reopen an Incident every ~15s tick."""

from datetime import datetime, timedelta, timezone

from app.correlation_engine.config import CorrelationEngineConfig
from app.correlation_engine.decide import OpenIncidentSnapshot, ThresholdState, decide
from app.correlation_engine.narrative import NarrativeInput, generate_summary, generate_title
from app.risk_engine.config.schema import RiskLevel
from app.schemas.recommendation import RecommendationPriority

CONFIG = CorrelationEngineConfig()


# --- opening: qualification + debounce ---


def test_does_not_qualify_below_trigger_level() -> None:
    state, decision = decide(
        level=RiskLevel.MODERATE,
        is_emergency_override=False,
        highest_active_priority=None,
        current_incident=None,
        previous_state=ThresholdState(),
        config=CONFIG,
    )
    assert decision.action == "none"
    assert state.consecutive_ticks_above == 0
    assert state.consecutive_ticks_below == 1


def test_does_not_open_on_a_single_tick_at_trigger_level() -> None:
    """Regression guard for the exact thrash scenario the architecture review flagged: one
    tick at the trigger level must not open an Incident by itself."""
    state, decision = decide(
        level=RiskLevel.HIGH,
        is_emergency_override=False,
        highest_active_priority=None,
        current_incident=None,
        previous_state=ThresholdState(),
        config=CONFIG,
    )
    assert decision.action == "none"
    assert state.consecutive_ticks_above == 1


def test_opens_after_min_ticks_to_open_consecutive_qualifying_ticks() -> None:
    state = ThresholdState()
    decision = None
    for _ in range(CONFIG.min_ticks_to_open):
        state, decision = decide(
            level=RiskLevel.HIGH,
            is_emergency_override=False,
            highest_active_priority=None,
            current_incident=None,
            previous_state=state,
            config=CONFIG,
        )
    assert decision.action == "open"
    assert decision.peak_risk_severity == RiskLevel.HIGH


def test_a_single_tick_drop_does_not_immediately_resolve_an_open_incident() -> None:
    incident = OpenIncidentSnapshot(peak_risk_severity=RiskLevel.HIGH)
    state, decision = decide(
        level=RiskLevel.MODERATE,
        is_emergency_override=False,
        highest_active_priority=None,
        current_incident=incident,
        previous_state=ThresholdState(consecutive_ticks_above=5),
        config=CONFIG,
    )
    assert decision.action == "keep_open"
    assert state.consecutive_ticks_below == 1


def test_resolves_after_min_ticks_to_resolve_consecutive_non_qualifying_ticks() -> None:
    incident = OpenIncidentSnapshot(peak_risk_severity=RiskLevel.HIGH)
    state = ThresholdState()
    decision = None
    for _ in range(CONFIG.min_ticks_to_resolve):
        state, decision = decide(
            level=RiskLevel.NORMAL,
            is_emergency_override=False,
            highest_active_priority=None,
            current_incident=incident,
            previous_state=state,
            config=CONFIG,
        )
    assert decision.action == "resolve"


# --- emergency bypass ---


def test_emergency_override_opens_immediately_bypassing_debounce() -> None:
    state, decision = decide(
        level=RiskLevel.CRITICAL,
        is_emergency_override=True,
        highest_active_priority=None,
        current_incident=None,
        previous_state=ThresholdState(),
        config=CONFIG,
    )
    assert decision.action == "open"
    assert state.consecutive_ticks_above == 1


def test_emergency_override_qualifies_even_below_the_configured_risk_level_trigger() -> None:
    state, decision = decide(
        level=RiskLevel.LOW,
        is_emergency_override=True,
        highest_active_priority=None,
        current_incident=None,
        previous_state=ThresholdState(),
        config=CONFIG,
    )
    assert decision.action == "open"


# --- recommendation-priority trigger ---


def test_critical_recommendation_qualifies_independent_of_risk_level() -> None:
    state = ThresholdState()
    decision = None
    for _ in range(CONFIG.min_ticks_to_open):
        state, decision = decide(
            level=RiskLevel.LOW,
            is_emergency_override=False,
            highest_active_priority=RecommendationPriority.CRITICAL,
            current_incident=None,
            previous_state=state,
            config=CONFIG,
        )
    assert decision.action == "open"


def test_moderate_recommendation_priority_alone_does_not_qualify() -> None:
    state, decision = decide(
        level=RiskLevel.LOW,
        is_emergency_override=False,
        highest_active_priority=RecommendationPriority.MODERATE,
        current_incident=None,
        previous_state=ThresholdState(),
        config=CONFIG,
    )
    assert decision.action == "none"


# --- peak severity, monotonic while open ---


def test_peak_risk_severity_rises_but_never_lowers_while_open() -> None:
    incident = OpenIncidentSnapshot(peak_risk_severity=RiskLevel.HIGH)
    _, decision = decide(
        level=RiskLevel.CRITICAL,
        is_emergency_override=False,
        highest_active_priority=None,
        current_incident=incident,
        previous_state=ThresholdState(consecutive_ticks_above=3),
        config=CONFIG,
    )
    assert decision.peak_risk_severity == RiskLevel.CRITICAL

    incident_at_peak = OpenIncidentSnapshot(peak_risk_severity=RiskLevel.CRITICAL)
    _, decision_two = decide(
        level=RiskLevel.HIGH,
        is_emergency_override=False,
        highest_active_priority=None,
        current_incident=incident_at_peak,
        previous_state=ThresholdState(consecutive_ticks_above=3),
        config=CONFIG,
    )
    assert decision_two.peak_risk_severity == RiskLevel.CRITICAL


# --- recurrence after resolve ---


def test_recurrence_after_resolve_opens_fresh_rather_than_reusing_old_incident() -> None:
    """decide() has no notion of a resolved-but-not-closed incident at all — IncidentService
    only ever passes it a snapshot of the currently OPEN incident (or None). A resolved old
    incident from an unrelated earlier episode must never be handed in here, so a new
    qualifying condition always produces a fresh "open", never a merge with old history."""
    state = ThresholdState()
    decision = None
    for _ in range(CONFIG.min_ticks_to_open):
        state, decision = decide(
            level=RiskLevel.HIGH,
            is_emergency_override=False,
            highest_active_priority=None,
            current_incident=None,  # no OPEN incident — an old resolved one is irrelevant here
            previous_state=state,
            config=CONFIG,
        )
    assert decision.action == "open"


# --- narrative generation ---

_NOW = datetime(2026, 7, 15, 14, 2, tzinfo=timezone.utc)


def test_generate_title_includes_classification_and_severity() -> None:
    narrative_input = NarrativeInput(
        zone_name="Crude Distillation Unit",
        classification="operational_episode",
        risk_severity_at_open=RiskLevel.CRITICAL,
        status="open",
        opened_at=_NOW,
        resolved_at=None,
    )
    title = generate_title(narrative_input)
    assert "Crude Distillation Unit" in title
    assert "Operational Episode" in title
    assert "CRITICAL" in title


def test_generate_title_omits_severity_for_manual_incidents_with_no_risk_assessment() -> None:
    narrative_input = NarrativeInput(
        zone_name="Tank Farm",
        classification="safety_incident",
        risk_severity_at_open=None,
        status="open",
        opened_at=_NOW,
        resolved_at=None,
    )
    assert "None" not in generate_title(narrative_input)


def test_generate_summary_includes_duration_when_resolved() -> None:
    narrative_input = NarrativeInput(
        zone_name="Crude Distillation Unit",
        classification="operational_episode",
        risk_severity_at_open=RiskLevel.CRITICAL,
        status="resolved",
        opened_at=_NOW,
        resolved_at=_NOW + timedelta(minutes=7),
        top_contributor_rationale="H2S concentration exceeded the critical threshold.",
        top_recommendation_title="Evacuate Personnel",
        recommendation_acknowledged=True,
    )
    summary = generate_summary(narrative_input)
    assert "H2S concentration exceeded" in summary
    assert "Evacuate Personnel" in summary
    assert "acknowledged" in summary
    assert "7 minutes" in summary


def test_generate_summary_marks_still_active_when_open() -> None:
    narrative_input = NarrativeInput(
        zone_name="Crude Distillation Unit",
        classification="operational_episode",
        risk_severity_at_open=RiskLevel.HIGH,
        status="open",
        opened_at=_NOW,
        resolved_at=None,
    )
    assert "Still active." in generate_summary(narrative_input)
