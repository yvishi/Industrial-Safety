"""Pure unit tests for the Compound Risk Engine's rule/aggregation logic — no DB, hand-built
ZoneFacts fixtures, mirroring how each rule is meant to be independently testable."""

from datetime import datetime, timezone
from uuid import uuid4

from app.risk_engine.config.defaults import DEFAULT_RISK_CONFIG
from app.risk_engine.config.schema import ConfidenceLevel, RiskCategory, RiskLevel, TrendDirection
from app.risk_engine.engine.aggregator import aggregate, build_category_breakdown
from app.risk_engine.engine.confidence import compute_confidence, confidence_label_for
from app.risk_engine.engine.explain import generate_explanation
from app.risk_engine.engine.trend import compute_trend
from app.risk_engine.facts import EquipmentFact, PermitFact, SensorFact, WorkerPresenceEntry, ZoneFacts
from app.risk_engine.rules import ALL_RULES
from app.risk_engine.rules.base import RuleResult
from app.risk_engine.rules.gas_hazard import RuleH2SCritical, RuleH2SElevated
from app.risk_engine.rules.permit_compliance import RuleHotWorkWithElevatedGas
from app.risk_engine.rules.process_safety import RuleEmergencyShutdownActive

NOW = datetime.now(timezone.utc)


def _sensor(sensor_type: str = "h2s", band: str = "normal", **overrides) -> SensorFact:
    defaults = dict(
        sensor_id=uuid4(),
        tag_number=f"{sensor_type.upper()}-1",
        sensor_type=sensor_type,
        unit_of_measure="ppm",
        status="active",
        last_value=10.0,
        last_reading_at=NOW,
        normal_min=0.0,
        normal_max=10.0,
        warning_min=None,
        warning_max=10.0,
        critical_min=None,
        critical_max=20.0,
        sampling_interval_seconds=5,
        equipment_id=None,
        effective_band=band,
        is_stale=False,
    )
    defaults.update(overrides)
    return SensorFact(**defaults)


def _permit(permit_type: str = "hot_work", **overrides) -> PermitFact:
    defaults = dict(
        permit_id=uuid4(),
        permit_number="PTW-2026-0001",
        permit_type=permit_type,
        required_isolation="gas_test_and_fire_watch",
        equipment_id=None,
        valid_until=None,
    )
    defaults.update(overrides)
    return PermitFact(**defaults)


def _equipment(**overrides) -> EquipmentFact:
    defaults = dict(
        equipment_id=uuid4(), tag_number="P-101A", equipment_type="pump", status="operational", criticality=None
    )
    defaults.update(overrides)
    return EquipmentFact(**defaults)


def _worker(**overrides) -> WorkerPresenceEntry:
    defaults = dict(worker_id=uuid4(), employee_id="EMP-001", role="field_operator")
    defaults.update(overrides)
    return WorkerPresenceEntry(**defaults)


def _facts(**overrides) -> ZoneFacts:
    defaults = dict(
        zone_id=uuid4(),
        zone_code="CDU-100",
        zone_name="Crude Distillation Unit",
        zone_type="crude_distillation",
        zone_category="process",
        emergency_shutdown_active=False,
        sensors=(),
        active_permits=(),
        equipment=(),
        workers_present=(),
        evaluated_at=NOW,
    )
    defaults.update(overrides)
    return ZoneFacts(**defaults)


# --- individual rule boundary tests ---


def test_rule_h2s_elevated_triggers_on_warning_band() -> None:
    facts = _facts(sensors=(_sensor("h2s", "warning"),))
    result = RuleH2SElevated().evaluate(facts, DEFAULT_RISK_CONFIG)
    assert result.triggered
    assert result.category == RiskCategory.GAS_HAZARD
    assert result.impact == DEFAULT_RISK_CONFIG.rule_weights.weights["RULE_H2S_ELEVATED"]
    assert not result.is_emergency_override


def test_rule_h2s_elevated_does_not_trigger_on_normal_band() -> None:
    facts = _facts(sensors=(_sensor("h2s", "normal"),))
    result = RuleH2SElevated().evaluate(facts, DEFAULT_RISK_CONFIG)
    assert not result.triggered
    assert result.impact == 0
    assert result.rationale == ""


def test_rule_h2s_critical_is_emergency_eligible() -> None:
    facts = _facts(sensors=(_sensor("h2s", "critical"),))
    result = RuleH2SCritical().evaluate(facts, DEFAULT_RISK_CONFIG)
    assert result.triggered
    assert result.is_emergency_override


def test_rule_hot_work_with_elevated_gas_is_compound() -> None:
    facts = _facts(active_permits=(_permit("hot_work"),), sensors=(_sensor("combustible_gas", "warning"),))
    result = RuleHotWorkWithElevatedGas().evaluate(facts, DEFAULT_RISK_CONFIG)
    assert result.triggered
    assert "PTW-2026-0001" in result.rationale
    assert {e.entity_type for e in result.referenced_entities} == {"permit", "sensor"}


def test_rule_hot_work_alone_does_not_trigger_without_gas_alarm() -> None:
    facts = _facts(active_permits=(_permit("hot_work"),), sensors=(_sensor("h2s", "normal"),))
    result = RuleHotWorkWithElevatedGas().evaluate(facts, DEFAULT_RISK_CONFIG)
    assert not result.triggered


def test_rule_emergency_shutdown_active() -> None:
    facts = _facts(emergency_shutdown_active=True)
    result = RuleEmergencyShutdownActive().evaluate(facts, DEFAULT_RISK_CONFIG)
    assert result.triggered
    assert result.is_emergency_override


# --- aggregator ---


def test_aggregator_clamps_score_at_100() -> None:
    facts = _facts(
        emergency_shutdown_active=True,
        sensors=(
            _sensor("h2s", "critical"),
            _sensor("combustible_gas", "critical"),
            _sensor("oxygen", "critical"),
            _sensor("smoke", "critical"),
        ),
    )
    results = [rule.evaluate(facts, DEFAULT_RISK_CONFIG) for rule in ALL_RULES]
    agg = aggregate(results, DEFAULT_RISK_CONFIG)
    assert agg.score == 100


def test_aggregator_emergency_override_forces_critical_and_floors_score() -> None:
    fake_result = RuleResult(
        rule_id="FAKE_LOW_IMPACT",
        triggered=True,
        category=RiskCategory.PROCESS_SAFETY,
        factor="fake",
        impact=5,
        severity="low",
        rationale="fake trigger",
        is_emergency_override=True,
    )
    agg = aggregate([fake_result], DEFAULT_RISK_CONFIG)
    assert agg.level == RiskLevel.CRITICAL
    assert agg.score >= DEFAULT_RISK_CONFIG.severity_bands.emergency_score_floor


def test_aggregator_emergency_override_never_lowers_a_higher_score() -> None:
    high_result = RuleResult(
        rule_id="FAKE_HIGH_IMPACT",
        triggered=True,
        category=RiskCategory.PROCESS_SAFETY,
        factor="fake",
        impact=95,
        severity="critical",
        rationale="fake trigger",
        is_emergency_override=True,
    )
    agg = aggregate([high_result], DEFAULT_RISK_CONFIG)
    assert agg.score == 95


def test_build_category_breakdown_returns_seven_entries_and_isolates_emergency() -> None:
    facts = _facts(emergency_shutdown_active=True, sensors=(_sensor("h2s", "warning"),))
    results = [rule.evaluate(facts, DEFAULT_RISK_CONFIG) for rule in ALL_RULES]
    breakdown = build_category_breakdown(results, DEFAULT_RISK_CONFIG)

    assert len(breakdown) == 7
    by_category = {b.category: b for b in breakdown}
    assert by_category[RiskCategory.PROCESS_SAFETY].level == RiskLevel.CRITICAL
    assert by_category[RiskCategory.ENVIRONMENTAL].score == 0
    assert by_category[RiskCategory.ENVIRONMENTAL].level == RiskLevel.NORMAL
    # A warning-band H2S reading alone should not be forced Critical by the unrelated ESD emergency.
    assert by_category[RiskCategory.GAS_HAZARD].level != RiskLevel.CRITICAL


# --- confidence ---


def test_compute_confidence_full_when_sensors_fresh_and_active() -> None:
    facts = _facts(sensors=(_sensor("h2s", "normal", is_stale=False, status="active"),))
    assert compute_confidence(facts, [], DEFAULT_RISK_CONFIG) == 100


def test_compute_confidence_penalizes_stale_sensor_feeding_triggered_rule() -> None:
    stale_sensor = _sensor("h2s", "critical", is_stale=True)
    facts = _facts(sensors=(stale_sensor,))
    triggered = [RuleH2SCritical().evaluate(facts, DEFAULT_RISK_CONFIG)]
    assert compute_confidence(facts, triggered, DEFAULT_RISK_CONFIG) < 100


def test_confidence_label_bands() -> None:
    assert confidence_label_for(90, DEFAULT_RISK_CONFIG) == ConfidenceLevel.HIGH
    assert confidence_label_for(60, DEFAULT_RISK_CONFIG) == ConfidenceLevel.MEDIUM
    assert confidence_label_for(10, DEFAULT_RISK_CONFIG) == ConfidenceLevel.LOW


# --- trend ---


def test_compute_trend() -> None:
    assert compute_trend(50, None) == (None, None)
    assert compute_trend(60, 50) == (10, TrendDirection.UP)
    assert compute_trend(40, 50) == (-10, TrendDirection.DOWN)
    assert compute_trend(50, 50) == (0, TrendDirection.FLAT)


# --- explanation ---


def test_generate_explanation_with_no_triggered_rules() -> None:
    text = generate_explanation("Test Zone", RiskLevel.NORMAL, 0, [], False, 3)
    assert "no elevated risk" in text


def test_generate_explanation_emergency_prefix() -> None:
    result = RuleResult(
        rule_id="RULE_X",
        triggered=True,
        category=RiskCategory.PROCESS_SAFETY,
        factor="X",
        impact=100,
        severity="critical",
        rationale="X happened.",
        is_emergency_override=True,
    )
    text = generate_explanation("Test Zone", RiskLevel.CRITICAL, 100, [result], True, 3)
    assert text.startswith("EMERGENCY CONDITION ACTIVE.")


# --- rule registry integrity ---


def test_all_registered_rules_have_a_configured_weight() -> None:
    for rule in ALL_RULES:
        assert rule.rule_id in DEFAULT_RISK_CONFIG.rule_weights.weights


def test_no_duplicate_rule_ids() -> None:
    ids = [r.rule_id for r in ALL_RULES]
    assert len(ids) == len(set(ids))
