"""Toxic-gas detection rules: H2S and oxygen depletion, warning and critical bands."""

from app.risk_engine.config.schema import RiskCategory, RiskEngineConfig
from app.risk_engine.facts import EntityRef, SensorFact, ZoneFacts
from app.risk_engine.rules.base import Rule, RuleResult


def _sensor_rationale(sensor: SensorFact) -> str:
    threshold = sensor.warning_min if sensor.warning_max is None else sensor.warning_max
    return (
        f"{sensor.tag_number} is reading {sensor.last_value} {sensor.unit_of_measure} "
        f"against a threshold of {threshold} {sensor.unit_of_measure}."
    )


class RuleH2SElevated(Rule):
    rule_id = "RULE_H2S_ELEVATED"
    category = RiskCategory.GAS_HAZARD
    default_severity = "moderate"
    description = "Detects early toxic-gas warning-band H2S readings before they reach critical."
    suggested_action = (
        "Increase atmospheric monitoring frequency and confirm ventilation is operating in the "
        "affected zone."
    )

    def evaluate(self, facts: ZoneFacts, config: RiskEngineConfig) -> RuleResult:
        matches = [
            s for s in facts.sensors_of_type("h2s") if s.effective_band == "warning"
        ]
        rationale = f"Elevated H2S detected: {_sensor_rationale(matches[0])}" if matches else ""
        return self._result(
            triggered=bool(matches),
            factor="Hydrogen Sulfide (H2S)",
            rationale=rationale,
            config=config,
            referenced_entities=tuple(
                EntityRef("sensor", s.sensor_id, s.tag_number) for s in matches
            ),
        )


class RuleH2SCritical(Rule):
    rule_id = "RULE_H2S_CRITICAL"
    category = RiskCategory.GAS_HAZARD
    default_severity = "critical"
    description = "Detects critical-band H2S readings representing an immediate toxic-gas hazard."
    suggested_action = (
        "Evacuate non-essential personnel immediately and dispatch a gas test team before any "
        "further work proceeds."
    )

    def evaluate(self, facts: ZoneFacts, config: RiskEngineConfig) -> RuleResult:
        matches = [
            s for s in facts.sensors_of_type("h2s") if s.effective_band == "critical"
        ]
        rationale = f"Critical H2S detected: {_sensor_rationale(matches[0])}" if matches else ""
        return self._result(
            triggered=bool(matches),
            factor="Hydrogen Sulfide (H2S)",
            rationale=rationale,
            config=config,
            referenced_entities=tuple(
                EntityRef("sensor", s.sensor_id, s.tag_number) for s in matches
            ),
        )


class RuleOxygenLowWarning(Rule):
    rule_id = "RULE_OXYGEN_LOW_WARNING"
    category = RiskCategory.GAS_HAZARD
    default_severity = "moderate"
    description = "Detects warning-band oxygen depletion readings."
    suggested_action = (
        "Increase atmospheric monitoring frequency and confirm ventilation is operating in the "
        "affected zone."
    )

    def evaluate(self, facts: ZoneFacts, config: RiskEngineConfig) -> RuleResult:
        matches = [
            s for s in facts.sensors_of_type("oxygen") if s.effective_band == "warning"
        ]
        rationale = f"Oxygen depletion detected: {_sensor_rationale(matches[0])}" if matches else ""
        return self._result(
            triggered=bool(matches),
            factor="Oxygen Depletion",
            rationale=rationale,
            config=config,
            referenced_entities=tuple(
                EntityRef("sensor", s.sensor_id, s.tag_number) for s in matches
            ),
        )


class RuleOxygenLowCritical(Rule):
    rule_id = "RULE_OXYGEN_LOW_CRITICAL"
    category = RiskCategory.GAS_HAZARD
    default_severity = "critical"
    description = "Detects critical-band oxygen depletion representing an immediate asphyxiation hazard."
    suggested_action = (
        "Evacuate non-essential personnel immediately and dispatch a gas test team before any "
        "further work proceeds."
    )

    def evaluate(self, facts: ZoneFacts, config: RiskEngineConfig) -> RuleResult:
        matches = [
            s for s in facts.sensors_of_type("oxygen") if s.effective_band == "critical"
        ]
        rationale = (
            f"Critical oxygen depletion detected: {_sensor_rationale(matches[0])}"
            if matches
            else ""
        )
        return self._result(
            triggered=bool(matches),
            factor="Oxygen Depletion",
            rationale=rationale,
            config=config,
            referenced_entities=tuple(
                EntityRef("sensor", s.sensor_id, s.tag_number) for s in matches
            ),
        )


RULES: list[Rule] = [
    RuleH2SElevated(),
    RuleH2SCritical(),
    RuleOxygenLowWarning(),
    RuleOxygenLowCritical(),
]
