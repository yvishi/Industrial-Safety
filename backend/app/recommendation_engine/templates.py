"""
Recommendation Rule -> Template mapping: the entire "reasoning" layer of the v1 Recommendation
Engine. Every triggered risk rule already carries the domain knowledge needed to know what an
operator should do about it (see each rule's own docstring in app/risk_engine/rules/) — so v1
deliberately does not build a second rule-evaluation engine on top. It just maps each of the 21
risk rule_ids onto one of a small set of operator-facing templates, generator.py groups
currently-triggered rules by template (deduplicating identical instructions instead of showing
near-duplicate cards), and computes priority/target/rationale from there.

A handful of templates are shared by more than one rule_id specifically because those rules
already carry byte-identical `suggested_action` text today (e.g. the three "elevated gas"
rules) — grouping them is a direct continuation of that existing duplication, not a new design
choice grafted on top.

Kept intentionally swappable: RULE_TEMPLATE_MAP + TEMPLATES is the entire seam a v2
Recommendation Rule Engine needs to replace (see generator.generate_candidates) without any
change to the API, schema, model, or lifecycle/reconciliation logic built on top of it.
"""

from dataclasses import dataclass

from app.risk_engine.config.schema import RiskCategory

# What a template's target_entity should resolve to. "zone" always resolves to the zone the
# assessment is for; the others look for the first EntityRef of that type among the
# contributing rules' source_refs, falling back to the zone if none is present.
TargetEntityType = str  # "sensor" | "equipment" | "permit" | "zone"


@dataclass(frozen=True)
class RecommendationTemplate:
    template_id: str
    category: RiskCategory
    title: str
    action_text: str
    expected_outcomes: tuple[str, ...]
    target_entity_type: TargetEntityType


TEMPLATES: dict[str, RecommendationTemplate] = {
    "increase_gas_monitoring": RecommendationTemplate(
        template_id="increase_gas_monitoring",
        category=RiskCategory.GAS_HAZARD,
        title="Increase Gas Monitoring",
        action_text=(
            "Increase atmospheric monitoring frequency and confirm ventilation is operating in "
            "the affected zone."
        ),
        expected_outcomes=("Reduce personnel exposure", "Prevent escalation to critical gas levels"),
        target_entity_type="sensor",
    ),
    "evacuate_personnel": RecommendationTemplate(
        template_id="evacuate_personnel",
        category=RiskCategory.GAS_HAZARD,
        title="Evacuate Personnel",
        action_text=(
            "Evacuate non-essential personnel immediately and dispatch a gas test team before "
            "any further work proceeds."
        ),
        expected_outcomes=("Reduce personnel exposure", "Prevent toxic exposure escalation"),
        target_entity_type="zone",
    ),
    "inspect_fire_detection": RecommendationTemplate(
        template_id="inspect_fire_detection",
        category=RiskCategory.FIRE_EXPLOSION,
        title="Inspect Fire Detection",
        action_text=(
            "Dispatch a visual inspection and confirm the fire detection system is functioning "
            "correctly in the affected zone."
        ),
        expected_outcomes=("Confirm fire detection integrity", "Prevent escalation to active fire"),
        target_entity_type="sensor",
    ),
    "activate_fire_response": RecommendationTemplate(
        template_id="activate_fire_response",
        category=RiskCategory.FIRE_EXPLOSION,
        title="Activate Fire Response",
        action_text="Activate fire response procedure and confirm fire water system pressure.",
        expected_outcomes=("Suppress active fire hazard", "Reduce personnel exposure"),
        target_entity_type="zone",
    ),
    "verify_maintenance_coverage": RecommendationTemplate(
        template_id="verify_maintenance_coverage",
        category=RiskCategory.EQUIPMENT,
        title="Verify Maintenance Coverage",
        action_text=(
            "Confirm this safety-critical equipment's maintenance is supervised and any "
            "compensating safety measures are in place."
        ),
        expected_outcomes=("Restore safe operating conditions", "Reduce likelihood of escalation"),
        target_entity_type="equipment",
    ),
    "review_equipment_availability": RecommendationTemplate(
        template_id="review_equipment_availability",
        category=RiskCategory.EQUIPMENT,
        title="Review Equipment Availability",
        action_text=(
            "Review the zone's operating posture given multiple out-of-service assets and "
            "confirm remaining equipment can safely cover the load."
        ),
        expected_outcomes=("Restore safe operating conditions", "Reduce likelihood of escalation"),
        target_entity_type="zone",
    ),
    "verify_permit_to_work": RecommendationTemplate(
        template_id="verify_permit_to_work",
        category=RiskCategory.EQUIPMENT,
        title="Verify Permit-to-Work",
        action_text="Verify a permit-to-work has been issued and approved for this maintenance activity.",
        expected_outcomes=("Restore permit compliance", "Reduce likelihood of escalation"),
        target_entity_type="equipment",
    ),
    "withdraw_personnel": RecommendationTemplate(
        template_id="withdraw_personnel",
        category=RiskCategory.PERSONNEL_EXPOSURE,
        title="Withdraw Personnel",
        action_text="Withdraw non-essential personnel from the zone until the gas reading returns to normal band.",
        expected_outcomes=("Reduce personnel exposure", "Prevent toxic exposure escalation"),
        target_entity_type="zone",
    ),
    "review_zone_occupancy": RecommendationTemplate(
        template_id="review_zone_occupancy",
        category=RiskCategory.PERSONNEL_EXPOSURE,
        title="Review Zone Occupancy",
        action_text="Review whether the current worker count in the zone is necessary and stagger non-essential tasks.",
        expected_outcomes=("Reduce personnel exposure", "Improve emergency evacuation capacity"),
        target_entity_type="zone",
    ),
    "assign_buddy_system": RecommendationTemplate(
        template_id="assign_buddy_system",
        category=RiskCategory.PERSONNEL_EXPOSURE,
        title="Assign a Buddy",
        action_text="Assign a second worker or establish active check-in monitoring for the lone worker in this zone.",
        expected_outcomes=("Reduce personnel exposure", "Ensure rapid response if an incident occurs"),
        target_entity_type="zone",
    ),
    "suspend_hot_work": RecommendationTemplate(
        template_id="suspend_hot_work",
        category=RiskCategory.PERMIT_COMPLIANCE,
        title="Suspend Hot Work",
        action_text="Suspend the hot work permit and evacuate non-essential personnel pending gas clearance.",
        expected_outcomes=("Prevent ignition source", "Reduce personnel exposure"),
        target_entity_type="permit",
    ),
    "record_isolation_standard": RecommendationTemplate(
        template_id="record_isolation_standard",
        category=RiskCategory.PERMIT_COMPLIANCE,
        title="Record Isolation Standard",
        action_text="Confirm and record the isolation standard for this confined space permit before work continues.",
        expected_outcomes=("Restore permit compliance", "Reduce likelihood of escalation"),
        target_entity_type="permit",
    ),
    "review_concurrent_permits": RecommendationTemplate(
        template_id="review_concurrent_permits",
        category=RiskCategory.PERMIT_COMPLIANCE,
        title="Review Concurrent Permits",
        action_text="Review whether concurrently active high-risk permits in this zone can be safely sequenced instead.",
        expected_outcomes=("Reduce likelihood of escalation", "Restore safe operating conditions"),
        target_entity_type="zone",
    ),
    "stabilize_process_temperature": RecommendationTemplate(
        template_id="stabilize_process_temperature",
        category=RiskCategory.PROCESS_SAFETY,
        title="Stabilize Process Temperature",
        action_text="Initiate temperature stabilization procedures and notify the process engineer on duty.",
        expected_outcomes=("Restore safe operating conditions", "Prevent equipment damage"),
        target_entity_type="sensor",
    ),
    "stabilize_process_pressure": RecommendationTemplate(
        template_id="stabilize_process_pressure",
        category=RiskCategory.PROCESS_SAFETY,
        title="Stabilize Process Pressure",
        action_text="Initiate pressure relief/stabilization procedures and notify the process engineer on duty.",
        expected_outcomes=("Restore safe operating conditions", "Prevent equipment damage"),
        target_entity_type="sensor",
    ),
    "inspect_equipment_vibration": RecommendationTemplate(
        template_id="inspect_equipment_vibration",
        category=RiskCategory.PROCESS_SAFETY,
        title="Inspect Equipment",
        action_text="Schedule a mechanical inspection of the affected asset to investigate the elevated vibration trend.",
        expected_outcomes=("Prevent equipment damage", "Reduce likelihood of escalation"),
        target_entity_type="sensor",
    ),
    "confirm_esd_response": RecommendationTemplate(
        template_id="confirm_esd_response",
        category=RiskCategory.PROCESS_SAFETY,
        title="Confirm ESD Response",
        action_text="Confirm the emergency shutdown response procedure is being followed and coordinate restart authorization.",
        expected_outcomes=("Restore safe operating conditions", "Reduce likelihood of escalation"),
        target_entity_type="zone",
    ),
}

# Every rule_id in app.risk_engine.rules.ALL_RULES must appear here exactly once — enforced by
# test_recommendation_engine.py::test_all_rules_have_a_template, mirroring how
# test_risk_engine.py enforces every rule has a configured weight.
RULE_TEMPLATE_MAP: dict[str, str] = {
    # Gas Hazard
    "RULE_H2S_ELEVATED": "increase_gas_monitoring",
    "RULE_H2S_CRITICAL": "evacuate_personnel",
    "RULE_OXYGEN_LOW_WARNING": "increase_gas_monitoring",
    "RULE_OXYGEN_LOW_CRITICAL": "evacuate_personnel",
    # Fire & Explosion
    "RULE_COMBUSTIBLE_GAS_ELEVATED": "increase_gas_monitoring",
    "RULE_COMBUSTIBLE_GAS_CRITICAL": "evacuate_personnel",
    "RULE_SMOKE_WARNING": "inspect_fire_detection",
    "RULE_SMOKE_CRITICAL": "activate_fire_response",
    # Equipment
    "RULE_SAFETY_CRITICAL_UNDER_MAINTENANCE": "verify_maintenance_coverage",
    "RULE_MULTIPLE_EQUIPMENT_DOWN": "review_equipment_availability",
    "RULE_MAINTENANCE_WITHOUT_ACTIVE_PERMIT": "verify_permit_to_work",
    # Personnel Exposure
    "RULE_WORKERS_PRESENT_DURING_GAS_ALARM": "withdraw_personnel",
    "RULE_HIGH_WORKER_DENSITY": "review_zone_occupancy",
    "RULE_LONE_WORKER_IN_HAZARDOUS_ZONE": "assign_buddy_system",
    # Permit Compliance
    "RULE_HOT_WORK_WITH_ELEVATED_GAS": "suspend_hot_work",
    "RULE_CONFINED_SPACE_WITHOUT_ISOLATION_RECORDED": "record_isolation_standard",
    "RULE_MULTIPLE_CONCURRENT_HIGH_RISK_PERMITS": "review_concurrent_permits",
    # Process Safety
    "RULE_PROCESS_TEMPERATURE_CRITICAL": "stabilize_process_temperature",
    "RULE_PROCESS_PRESSURE_CRITICAL": "stabilize_process_pressure",
    "RULE_VIBRATION_WARNING": "inspect_equipment_vibration",
    "RULE_EMERGENCY_SHUTDOWN_ACTIVE": "confirm_esd_response",
}
