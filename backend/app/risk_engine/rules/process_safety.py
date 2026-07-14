"""Process safety rules: temperature/pressure excursions, vibration trending, and the
emergency shutdown state flag."""

from app.risk_engine.config.schema import RiskCategory, RiskEngineConfig
from app.risk_engine.facts import EntityRef, SensorFact, ZoneFacts
from app.risk_engine.rules.base import Rule, RuleResult


def _sensor_rationale(sensor: SensorFact) -> str:
    return f"{sensor.tag_number} is reading {sensor.last_value} {sensor.unit_of_measure}."


class RuleProcessTemperatureCritical(Rule):
    rule_id = "RULE_PROCESS_TEMPERATURE_CRITICAL"
    category = RiskCategory.PROCESS_SAFETY
    default_severity = "critical"
    description = "Detects critical-band process temperature excursions."

    def evaluate(self, facts: ZoneFacts, config: RiskEngineConfig) -> RuleResult:
        matches = [
            s for s in facts.sensors_of_type("temperature") if s.effective_band == "critical"
        ]
        rationale = f"Critical temperature excursion: {_sensor_rationale(matches[0])}" if matches else ""
        return self._result(
            triggered=bool(matches),
            factor="Process Temperature Excursion",
            rationale=rationale,
            config=config,
            referenced_entities=tuple(
                EntityRef("sensor", s.sensor_id, s.tag_number) for s in matches
            ),
        )


class RuleProcessPressureCritical(Rule):
    rule_id = "RULE_PROCESS_PRESSURE_CRITICAL"
    category = RiskCategory.PROCESS_SAFETY
    default_severity = "critical"
    description = "Detects critical-band process pressure excursions."

    def evaluate(self, facts: ZoneFacts, config: RiskEngineConfig) -> RuleResult:
        matches = [
            s for s in facts.sensors_of_type("pressure") if s.effective_band == "critical"
        ]
        rationale = f"Critical pressure excursion: {_sensor_rationale(matches[0])}" if matches else ""
        return self._result(
            triggered=bool(matches),
            factor="Process Pressure Excursion",
            rationale=rationale,
            config=config,
            referenced_entities=tuple(
                EntityRef("sensor", s.sensor_id, s.tag_number) for s in matches
            ),
        )


class RuleVibrationWarning(Rule):
    rule_id = "RULE_VIBRATION_WARNING"
    category = RiskCategory.PROCESS_SAFETY
    default_severity = "moderate"
    description = (
        "Detects elevated vibration readings (warning or critical band) as a leading indicator "
        "of mechanical degradation — not an emergency trigger, so both bands are handled by a "
        "single rule."
    )

    def evaluate(self, facts: ZoneFacts, config: RiskEngineConfig) -> RuleResult:
        matches = [
            s
            for s in facts.sensors_of_type("vibration")
            if s.effective_band in ("warning", "critical")
        ]
        rationale = f"Elevated vibration: {_sensor_rationale(matches[0])}" if matches else ""
        return self._result(
            triggered=bool(matches),
            factor="Elevated Vibration",
            rationale=rationale,
            config=config,
            referenced_entities=tuple(
                EntityRef("sensor", s.sensor_id, s.tag_number) for s in matches
            ),
        )


class RuleEmergencyShutdownActive(Rule):
    rule_id = "RULE_EMERGENCY_SHUTDOWN_ACTIVE"
    category = RiskCategory.PROCESS_SAFETY
    default_severity = "critical"
    description = "Detects that the zone's emergency shutdown system is currently active."

    def evaluate(self, facts: ZoneFacts, config: RiskEngineConfig) -> RuleResult:
        triggered = facts.emergency_shutdown_active is True
        rationale = f"{facts.zone_name}'s emergency shutdown system is ACTIVE." if triggered else ""
        return self._result(
            triggered=triggered,
            factor="Emergency Shutdown Active",
            rationale=rationale,
            config=config,
        )


RULES: list[Rule] = [
    RuleProcessTemperatureCritical(),
    RuleProcessPressureCritical(),
    RuleVibrationWarning(),
    RuleEmergencyShutdownActive(),
]
