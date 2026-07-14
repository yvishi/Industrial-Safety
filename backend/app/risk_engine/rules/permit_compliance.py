"""Permit-to-work compliance rules: hot work against elevated gas readings, confined-space
isolation record-keeping, and concurrent high-risk permit load."""

from app.risk_engine.config.schema import RiskCategory, RiskEngineConfig
from app.risk_engine.facts import EntityRef, ZoneFacts
from app.risk_engine.rules.base import Rule, RuleResult

_GAS_SENSOR_TYPES = ("h2s", "combustible_gas", "oxygen")
_HIGH_RISK_PERMIT_TYPES = ("hot_work", "confined_space", "line_breaking", "excavation")


class RuleHotWorkWithElevatedGas(Rule):
    rule_id = "RULE_HOT_WORK_WITH_ELEVATED_GAS"
    category = RiskCategory.PERMIT_COMPLIANCE
    default_severity = "critical"
    description = "Detects an active hot work permit while a gas sensor in the zone is in warning or critical band."
    suggested_action = "Suspend the hot work permit and evacuate non-essential personnel pending gas clearance."

    def evaluate(self, facts: ZoneFacts, config: RiskEngineConfig) -> RuleResult:
        hot_work_permits = [p for p in facts.active_permits if p.permit_type == "hot_work"]
        alarming_sensors = [
            s
            for s in facts.sensors
            if s.sensor_type in _GAS_SENSOR_TYPES and s.effective_band in ("warning", "critical")
        ]
        triggered = bool(hot_work_permits) and bool(alarming_sensors)
        rationale = (
            f"Hot work permit {hot_work_permits[0].permit_number} is active while "
            f"{alarming_sensors[0].tag_number} is in {alarming_sensors[0].effective_band} band."
            if triggered
            else ""
        )
        entities = tuple(
            EntityRef("permit", p.permit_id, p.permit_number) for p in hot_work_permits
        ) + tuple(EntityRef("sensor", s.sensor_id, s.tag_number) for s in alarming_sensors)
        return self._result(
            triggered=triggered,
            factor="Hot Work with Elevated Gas Reading",
            rationale=rationale,
            config=config,
            referenced_entities=entities,
        )


class RuleConfinedSpaceWithoutIsolationRecorded(Rule):
    rule_id = "RULE_CONFINED_SPACE_WITHOUT_ISOLATION_RECORDED"
    category = RiskCategory.PERMIT_COMPLIANCE
    default_severity = "moderate"
    description = "Detects an active confined space permit with no isolation standard recorded."

    def evaluate(self, facts: ZoneFacts, config: RiskEngineConfig) -> RuleResult:
        matches = [
            p
            for p in facts.active_permits
            if p.permit_type == "confined_space" and p.required_isolation is None
        ]
        rationale = (
            f"Confined space permit {matches[0].permit_number} has no isolation standard recorded."
            if matches
            else ""
        )
        return self._result(
            triggered=bool(matches),
            factor="Confined Space Without Isolation Record",
            rationale=rationale,
            config=config,
            referenced_entities=tuple(
                EntityRef("permit", p.permit_id, p.permit_number) for p in matches
            ),
        )


class RuleMultipleConcurrentHighRiskPermits(Rule):
    rule_id = "RULE_MULTIPLE_CONCURRENT_HIGH_RISK_PERMITS"
    category = RiskCategory.PERMIT_COMPLIANCE
    default_severity = "moderate"
    description = "Detects when several high-risk permits are active in the zone at the same time."

    def evaluate(self, facts: ZoneFacts, config: RiskEngineConfig) -> RuleResult:
        high_risk = [p for p in facts.active_permits if p.permit_type in _HIGH_RISK_PERMIT_TYPES]
        triggered = len(high_risk) >= config.thresholds.multiple_high_risk_permits_threshold
        rationale = (
            f"{len(high_risk)} high-risk permits are concurrently active in {facts.zone_name}."
            if triggered
            else ""
        )
        return self._result(
            triggered=triggered,
            factor="Multiple Concurrent High-Risk Permits",
            rationale=rationale,
            config=config,
            referenced_entities=tuple(
                EntityRef("permit", p.permit_id, p.permit_number) for p in high_risk
            ),
        )


RULES: list[Rule] = [
    RuleHotWorkWithElevatedGas(),
    RuleConfinedSpaceWithoutIsolationRecorded(),
    RuleMultipleConcurrentHighRiskPermits(),
]
