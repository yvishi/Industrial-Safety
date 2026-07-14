"""Fire and explosion detection rules: combustible gas (LEL) and smoke, warning and critical bands."""

from app.risk_engine.config.schema import RiskCategory, RiskEngineConfig
from app.risk_engine.facts import EntityRef, SensorFact, ZoneFacts
from app.risk_engine.rules.base import Rule, RuleResult


def _sensor_rationale(sensor: SensorFact) -> str:
    threshold = sensor.warning_min if sensor.warning_max is None else sensor.warning_max
    return (
        f"{sensor.tag_number} is reading {sensor.last_value} {sensor.unit_of_measure} "
        f"against a threshold of {threshold} {sensor.unit_of_measure}."
    )


class RuleCombustibleGasElevated(Rule):
    rule_id = "RULE_COMBUSTIBLE_GAS_ELEVATED"
    category = RiskCategory.FIRE_EXPLOSION
    default_severity = "moderate"
    description = "Detects warning-band combustible gas (LEL) readings before they reach critical."
    suggested_action = (
        "Increase atmospheric monitoring frequency and confirm ventilation is operating in the "
        "affected zone."
    )

    def evaluate(self, facts: ZoneFacts, config: RiskEngineConfig) -> RuleResult:
        matches = [
            s for s in facts.sensors_of_type("combustible_gas") if s.effective_band == "warning"
        ]
        rationale = (
            f"Elevated combustible gas detected: {_sensor_rationale(matches[0])}" if matches else ""
        )
        return self._result(
            triggered=bool(matches),
            factor="Combustible Gas (LEL)",
            rationale=rationale,
            config=config,
            referenced_entities=tuple(
                EntityRef("sensor", s.sensor_id, s.tag_number) for s in matches
            ),
        )


class RuleCombustibleGasCritical(Rule):
    rule_id = "RULE_COMBUSTIBLE_GAS_CRITICAL"
    category = RiskCategory.FIRE_EXPLOSION
    default_severity = "critical"
    description = "Detects critical-band combustible gas (LEL) readings representing an imminent explosion hazard."
    suggested_action = (
        "Evacuate non-essential personnel immediately and dispatch a gas test team before any "
        "further work proceeds."
    )

    def evaluate(self, facts: ZoneFacts, config: RiskEngineConfig) -> RuleResult:
        matches = [
            s for s in facts.sensors_of_type("combustible_gas") if s.effective_band == "critical"
        ]
        rationale = (
            f"Critical combustible gas detected: {_sensor_rationale(matches[0])}" if matches else ""
        )
        return self._result(
            triggered=bool(matches),
            factor="Combustible Gas (LEL)",
            rationale=rationale,
            config=config,
            referenced_entities=tuple(
                EntityRef("sensor", s.sensor_id, s.tag_number) for s in matches
            ),
        )


class RuleSmokeWarning(Rule):
    rule_id = "RULE_SMOKE_WARNING"
    category = RiskCategory.FIRE_EXPLOSION
    default_severity = "moderate"
    description = "Detects warning-band smoke detector readings."
    suggested_action = (
        "Dispatch a visual inspection and confirm the fire detection system is functioning "
        "correctly in the affected zone."
    )

    def evaluate(self, facts: ZoneFacts, config: RiskEngineConfig) -> RuleResult:
        matches = [
            s for s in facts.sensors_of_type("smoke") if s.effective_band == "warning"
        ]
        rationale = f"Smoke detected: {_sensor_rationale(matches[0])}" if matches else ""
        return self._result(
            triggered=bool(matches),
            factor="Smoke Detection",
            rationale=rationale,
            config=config,
            referenced_entities=tuple(
                EntityRef("sensor", s.sensor_id, s.tag_number) for s in matches
            ),
        )


class RuleSmokeCritical(Rule):
    rule_id = "RULE_SMOKE_CRITICAL"
    category = RiskCategory.FIRE_EXPLOSION
    default_severity = "critical"
    description = "Detects critical-band smoke detector readings representing an active fire hazard."
    suggested_action = (
        "Activate fire response procedure and confirm fire water system pressure."
    )

    def evaluate(self, facts: ZoneFacts, config: RiskEngineConfig) -> RuleResult:
        matches = [
            s for s in facts.sensors_of_type("smoke") if s.effective_band == "critical"
        ]
        rationale = f"Critical smoke levels detected: {_sensor_rationale(matches[0])}" if matches else ""
        return self._result(
            triggered=bool(matches),
            factor="Smoke Detection",
            rationale=rationale,
            config=config,
            referenced_entities=tuple(
                EntityRef("sensor", s.sensor_id, s.tag_number) for s in matches
            ),
        )


RULES: list[Rule] = [
    RuleCombustibleGasElevated(),
    RuleCombustibleGasCritical(),
    RuleSmokeWarning(),
    RuleSmokeCritical(),
]
