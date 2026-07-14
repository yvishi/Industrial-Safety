"""Pure unit tests for the Recommendation Engine's template mapping and candidate generation —
no DB, hand-built RiskAssessment fixtures, mirroring test_risk_engine.py's style."""

from datetime import datetime, timezone
from uuid import uuid4

from app.recommendation_engine.generator import generate_candidates
from app.recommendation_engine.templates import RULE_TEMPLATE_MAP, TEMPLATES
from app.risk_engine.config.schema import ConfidenceLevel, RiskCategory, RiskLevel
from app.risk_engine.rules import ALL_RULES
from app.schemas.risk import CategoryRisk, EntityRefRead, RiskAssessment, RiskContributor

NOW = datetime.now(timezone.utc)


def _contributor(rule_id: str, *, severity: str = "moderate", impact: int = 15, source_refs=None, **overrides) -> RiskContributor:
    defaults = dict(
        rule_id=rule_id,
        category=RiskCategory.GAS_HAZARD,
        factor="Test Factor",
        impact=impact,
        severity=severity,
        rationale=f"{rule_id} triggered.",
        source_refs=source_refs or [],
    )
    defaults.update(overrides)
    return RiskContributor(**defaults)


def _assessment(contributors: list[RiskContributor], *, is_emergency_override: bool = False, **overrides) -> RiskAssessment:
    defaults = dict(
        zone_id=uuid4(),
        zone_name="Crude Distillation Unit",
        engine_version="CRE-v1.0.0",
        score=30,
        level=RiskLevel.MODERATE,
        is_emergency_override=is_emergency_override,
        confidence_score=100,
        confidence_label=ConfidenceLevel.HIGH,
        categories=[
            CategoryRisk(category=c, score=0, level=RiskLevel.NORMAL, top_contributor=None) for c in RiskCategory
        ],
        contributors=contributors,
        recommended_actions=[],
        previous_score=None,
        score_delta=None,
        trend_direction=None,
        evaluation_duration_ms=1,
        explanation="Test explanation.",
        evaluated_at=NOW,
    )
    defaults.update(overrides)
    return RiskAssessment(**defaults)


# --- registry integrity ---


def test_all_rules_have_a_template() -> None:
    for rule in ALL_RULES:
        assert rule.rule_id in RULE_TEMPLATE_MAP, f"{rule.rule_id} has no recommendation template"


def test_no_orphan_template_ids() -> None:
    for template_id in RULE_TEMPLATE_MAP.values():
        assert template_id in TEMPLATES


def test_no_duplicate_rule_mappings() -> None:
    assert len(RULE_TEMPLATE_MAP) == len(ALL_RULES)


# --- candidate generation ---


def test_generate_candidates_empty_when_nothing_triggered() -> None:
    assert generate_candidates(_assessment([])) == []


def test_generate_candidates_merges_rules_sharing_a_template() -> None:
    # RULE_H2S_ELEVATED and RULE_OXYGEN_LOW_WARNING both map to increase_gas_monitoring.
    contributors = [
        _contributor("RULE_H2S_ELEVATED", severity="moderate"),
        _contributor("RULE_OXYGEN_LOW_WARNING", severity="moderate"),
    ]
    candidates = generate_candidates(_assessment(contributors))
    assert len(candidates) == 1
    assert candidates[0].template_id == "increase_gas_monitoring"
    assert candidates[0].source_rule_ids == ("RULE_H2S_ELEVATED", "RULE_OXYGEN_LOW_WARNING")


def test_generate_candidates_priority_matches_worst_contributor_severity() -> None:
    contributors = [
        _contributor("RULE_H2S_ELEVATED", severity="moderate"),
        _contributor("RULE_OXYGEN_LOW_WARNING", severity="low"),
    ]
    candidates = generate_candidates(_assessment(contributors))
    assert candidates[0].priority == "moderate"


def test_generate_candidates_emergency_override_forces_critical_priority() -> None:
    contributors = [_contributor("RULE_HIGH_WORKER_DENSITY", severity="moderate")]
    candidates = generate_candidates(_assessment(contributors, is_emergency_override=True))
    assert candidates[0].priority == "critical"


def test_generate_candidates_target_entity_resolves_matching_type() -> None:
    permit_ref = EntityRefRead(entity_type="permit", entity_id=uuid4(), label="HW-2044")
    sensor_ref = EntityRefRead(entity_type="sensor", entity_id=uuid4(), label="LEL-1")
    contributors = [
        _contributor("RULE_HOT_WORK_WITH_ELEVATED_GAS", severity="critical", source_refs=[permit_ref, sensor_ref])
    ]
    candidates = generate_candidates(_assessment(contributors))
    assert candidates[0].template_id == "suspend_hot_work"
    assert candidates[0].target_entity.entity_type == "permit"
    assert candidates[0].target_entity.label == "HW-2044"


def test_generate_candidates_target_entity_falls_back_to_zone() -> None:
    # RULE_HIGH_WORKER_DENSITY carries no referenced entities at all.
    contributors = [_contributor("RULE_HIGH_WORKER_DENSITY", severity="moderate")]
    assessment = _assessment(contributors)
    candidates = generate_candidates(assessment)
    assert candidates[0].target_entity.entity_type == "zone"
    assert candidates[0].target_entity.entity_id == assessment.zone_id
    assert candidates[0].target_entity.label == assessment.zone_name


def test_generate_candidates_evacuate_personnel_targets_zone_not_sensor() -> None:
    # Per product decision: evacuation-style recommendations target the zone, not the
    # individual sensor that tripped, even though the rule does expose a sensor EntityRef.
    sensor_ref = EntityRefRead(entity_type="sensor", entity_id=uuid4(), label="H2S-1")
    contributors = [_contributor("RULE_H2S_CRITICAL", severity="critical", source_refs=[sensor_ref])]
    assessment = _assessment(contributors, is_emergency_override=True)
    candidates = generate_candidates(assessment)
    assert candidates[0].template_id == "evacuate_personnel"
    assert candidates[0].target_entity.entity_type == "zone"


def test_generate_candidates_sorted_most_urgent_first() -> None:
    contributors = [
        _contributor("RULE_HIGH_WORKER_DENSITY", severity="moderate", impact=8),
        _contributor("RULE_LONE_WORKER_IN_HAZARDOUS_ZONE", severity="moderate", impact=10),
        _contributor("RULE_H2S_CRITICAL", severity="critical", impact=35),
    ]
    candidates = generate_candidates(_assessment(contributors))
    assert candidates[0].priority == "critical"
    assert candidates[0].template_id == "evacuate_personnel"


def test_generate_candidates_expected_outcomes_are_operator_facing_not_scores() -> None:
    contributors = [_contributor("RULE_H2S_CRITICAL", severity="critical")]
    candidates = generate_candidates(_assessment(contributors))
    assert candidates[0].expected_outcomes
    assert all(isinstance(o, str) for o in candidates[0].expected_outcomes)
