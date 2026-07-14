"""Confidence scoring: a deterministic, formulaic 0-100 data-quality trust figure — NOT
probabilistic/ML. Answers "how much should you trust this zone's score", not "how risky is
this zone".
"""

from app.risk_engine.config.schema import ConfidenceLevel, RiskEngineConfig
from app.risk_engine.facts import ZoneFacts
from app.risk_engine.rules.base import RuleResult

_BAD_STATUSES = ("faulted", "under_calibration")
_PER_SENSOR_DEDUCTION = 15
_MAX_BASE_DEDUCTION = 60
_PER_TRIGGERED_SENSOR_PENALTY = 10


def _is_bad(status: str, is_stale: bool) -> bool:
    return status in _BAD_STATUSES or is_stale


def compute_confidence(facts: ZoneFacts, triggered: list[RuleResult], config: RiskEngineConfig) -> int:
    """Two components:
    1. base_quality: 100 minus a capped deduction (15 points per "bad" sensor in the whole
       zone, capped at 60 total deduction).
    2. triggered_penalty: an uncapped extra deduction of 10 points per "bad" sensor that was
       actually referenced by a triggered rule.
    Return max(0, min(100, base_quality - triggered_penalty)).
    """
    bad_sensor_count = sum(1 for s in facts.sensors if _is_bad(s.status, s.is_stale))
    base_deduction = min(_MAX_BASE_DEDUCTION, _PER_SENSOR_DEDUCTION * bad_sensor_count)
    base_quality = 100 - base_deduction

    sensors_by_id = {s.sensor_id: s for s in facts.sensors}
    referenced_bad_sensor_ids: set = set()
    for result in triggered:
        for entity in result.referenced_entities:
            if entity.entity_type != "sensor":
                continue
            sensor = sensors_by_id.get(entity.entity_id)
            if sensor is not None and _is_bad(sensor.status, sensor.is_stale):
                referenced_bad_sensor_ids.add(sensor.sensor_id)

    triggered_penalty = _PER_TRIGGERED_SENSOR_PENALTY * len(referenced_bad_sensor_ids)

    return max(0, min(100, base_quality - triggered_penalty))


def confidence_label_for(score: int, config: RiskEngineConfig) -> ConfidenceLevel:
    bands = config.confidence_bands
    if score >= bands.high_min:
        return ConfidenceLevel.HIGH
    if score >= bands.medium_min:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW
