"""Personnel exposure rules: worker presence during gas alarms, worker density, and lone
workers in hazardous zones. These deliberately overlap with gas_hazard/fire_explosion — "a
hazard exists" and "people are exposed to it" are different questions, both worth scoring."""

from app.risk_engine.config.schema import RiskCategory, RiskEngineConfig
from app.risk_engine.facts import EntityRef, ZoneFacts
from app.risk_engine.rules.base import Rule, RuleResult

_GAS_SENSOR_TYPES = ("h2s", "combustible_gas", "oxygen")


class RuleWorkersPresentDuringGasAlarm(Rule):
    rule_id = "RULE_WORKERS_PRESENT_DURING_GAS_ALARM"
    category = RiskCategory.PERSONNEL_EXPOSURE
    default_severity = "high"
    description = "Detects workers present in a zone while a gas sensor is in warning or critical band."

    def evaluate(self, facts: ZoneFacts, config: RiskEngineConfig) -> RuleResult:
        alarming = [
            s
            for s in facts.sensors
            if s.sensor_type in _GAS_SENSOR_TYPES and s.effective_band in ("warning", "critical")
        ]
        triggered = bool(facts.workers_present) and bool(alarming)
        rationale = (
            f"{len(facts.workers_present)} worker(s) present in {facts.zone_name} while "
            f"{alarming[0].tag_number} is in {alarming[0].effective_band} band."
            if triggered
            else ""
        )
        return self._result(
            triggered=triggered,
            factor="Workers Present During Gas Alarm",
            rationale=rationale,
            config=config,
            referenced_entities=tuple(
                EntityRef("sensor", s.sensor_id, s.tag_number) for s in alarming
            ),
        )


class RuleHighWorkerDensity(Rule):
    rule_id = "RULE_HIGH_WORKER_DENSITY"
    category = RiskCategory.PERSONNEL_EXPOSURE
    default_severity = "moderate"
    description = "Detects when the number of workers present in a zone exceeds the density threshold."

    def evaluate(self, facts: ZoneFacts, config: RiskEngineConfig) -> RuleResult:
        count = len(facts.workers_present)
        triggered = count >= config.thresholds.high_worker_density_threshold
        rationale = (
            f"{count} workers are present in {facts.zone_name}, at or above the density "
            f"threshold of {config.thresholds.high_worker_density_threshold}."
            if triggered
            else ""
        )
        return self._result(
            triggered=triggered,
            factor="High Worker Density",
            rationale=rationale,
            config=config,
        )


class RuleLoneWorkerInHazardousZone(Rule):
    rule_id = "RULE_LONE_WORKER_IN_HAZARDOUS_ZONE"
    category = RiskCategory.PERSONNEL_EXPOSURE
    default_severity = "moderate"
    description = (
        "Detects a single worker alone in a process or safety-systems zone that contains "
        "safety-critical equipment."
    )

    def evaluate(self, facts: ZoneFacts, config: RiskEngineConfig) -> RuleResult:
        triggered = (
            len(facts.workers_present) == 1
            and facts.zone_category in ("process", "safety_systems")
            and facts.highest_equipment_criticality == "safety_critical"
        )
        rationale = (
            f"A lone worker is present in {facts.zone_name}, a {facts.zone_category} zone "
            f"containing safety-critical equipment."
            if triggered
            else ""
        )
        return self._result(
            triggered=triggered,
            factor="Lone Worker in Hazardous Zone",
            rationale=rationale,
            config=config,
        )


RULES: list[Rule] = [
    RuleWorkersPresentDuringGasAlarm(),
    RuleHighWorkerDensity(),
    RuleLoneWorkerInHazardousZone(),
]
