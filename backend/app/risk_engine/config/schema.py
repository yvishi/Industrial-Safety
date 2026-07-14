"""
Risk Engine configuration schema: the tunable vocabulary and numbers a rule reasons with —
weights, severity bands, confidence bands, emergency-rule designations. Config-as-code, plain
Pydantic validated at import time, no DB — mirrors app/plant_types/schema.py's existing
pattern for exactly the same reason: a domain expert should be able to retune these values by
reading and editing Python, not by hunting through rule logic for magic numbers.

RiskCategory/RiskLevel/ConfidenceLevel/TrendDirection live here (not in schemas/risk.py)
because they are the engine's own taxonomy — schemas/risk.py imports them, the same way
schemas/zone.py imports ZoneCategory from app.plant_types.schema.
"""

from enum import Enum

from pydantic import BaseModel, model_validator


class RiskCategory(str, Enum):
    """
    The seven risk lenses the engine reasons under. Every rule belongs to exactly one.

    ENVIRONMENTAL is deliberately reserved with zero rules in v1: the current sensor catalog
    (temperature/pressure/flow/level/h2s/combustible_gas/oxygen/vibration/valve_position/smoke)
    has no emissions/spill/ecological instrumentation, so labeling process-integrity sensors
    "environmental" would be a misnomer. It always reports Normal until such sensors exist.
    """

    GAS_HAZARD = "gas_hazard"
    FIRE_EXPLOSION = "fire_explosion"
    EQUIPMENT = "equipment"
    PERSONNEL_EXPOSURE = "personnel_exposure"
    PERMIT_COMPLIANCE = "permit_compliance"
    ENVIRONMENTAL = "environmental"
    PROCESS_SAFETY = "process_safety"


class RiskLevel(str, Enum):
    NORMAL = "normal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TrendDirection(str, Enum):
    UP = "up"
    DOWN = "down"
    FLAT = "flat"


class SeverityBandsConfig(BaseModel):
    """Score (0-100) -> RiskLevel cutoffs. Each bound is the score AT OR ABOVE which that
    level applies; anything below normal_max is Normal."""

    normal_max: int = 20
    low_max: int = 40
    moderate_max: int = 60
    high_max: int = 80
    # Score floor forced onto a zone whenever any emergency-override rule triggers.
    emergency_score_floor: int = 90

    @model_validator(mode="after")
    def _ordered(self) -> "SeverityBandsConfig":
        if not (0 <= self.normal_max < self.low_max < self.moderate_max < self.high_max <= 100):
            raise ValueError(
                "severity bands must satisfy 0 <= normal_max < low_max < moderate_max < high_max <= 100"
            )
        if not (self.high_max <= self.emergency_score_floor <= 100):
            raise ValueError("emergency_score_floor must sit between high_max and 100")
        return self


class ConfidenceBandsConfig(BaseModel):
    """Confidence score (0-100) -> ConfidenceLevel cutoffs."""

    high_min: int = 80
    medium_min: int = 50

    @model_validator(mode="after")
    def _ordered(self) -> "ConfidenceBandsConfig":
        if not (0 <= self.medium_min < self.high_min <= 100):
            raise ValueError("confidence bands must satisfy 0 <= medium_min < high_min <= 100")
        return self


class RuleWeightsConfig(BaseModel):
    """Per-rule score contribution when triggered. Every rule in ALL_RULES must have an entry
    here — enforced by a unit test (test_risk_engine.py), not at import time, to avoid a
    config<->rules import cycle (config must not import from rules)."""

    weights: dict[str, int] = {
        # Gas Hazard
        "RULE_H2S_ELEVATED": 15,
        "RULE_H2S_CRITICAL": 35,
        "RULE_OXYGEN_LOW_WARNING": 15,
        "RULE_OXYGEN_LOW_CRITICAL": 35,
        # Fire & Explosion
        "RULE_COMBUSTIBLE_GAS_ELEVATED": 15,
        "RULE_COMBUSTIBLE_GAS_CRITICAL": 35,
        "RULE_SMOKE_WARNING": 15,
        "RULE_SMOKE_CRITICAL": 35,
        # Equipment
        "RULE_SAFETY_CRITICAL_UNDER_MAINTENANCE": 20,
        "RULE_MULTIPLE_EQUIPMENT_DOWN": 10,
        "RULE_MAINTENANCE_WITHOUT_ACTIVE_PERMIT": 18,
        # Personnel Exposure
        "RULE_WORKERS_PRESENT_DURING_GAS_ALARM": 15,
        "RULE_HIGH_WORKER_DENSITY": 8,
        "RULE_LONE_WORKER_IN_HAZARDOUS_ZONE": 10,
        # Permit Compliance
        "RULE_HOT_WORK_WITH_ELEVATED_GAS": 25,
        "RULE_CONFINED_SPACE_WITHOUT_ISOLATION_RECORDED": 15,
        "RULE_MULTIPLE_CONCURRENT_HIGH_RISK_PERMITS": 10,
        # Process Safety
        "RULE_PROCESS_TEMPERATURE_CRITICAL": 20,
        "RULE_PROCESS_PRESSURE_CRITICAL": 20,
        "RULE_VIBRATION_WARNING": 12,
        "RULE_EMERGENCY_SHUTDOWN_ACTIVE": 100,
    }


class StalenessConfig(BaseModel):
    # A sensor is "stale" once its last reading is older than this many sampling intervals.
    stale_multiplier: float = 3.0


class ThresholdsConfig(BaseModel):
    multiple_equipment_down_threshold: int = 2
    high_worker_density_threshold: int = 5
    multiple_high_risk_permits_threshold: int = 2


class EmergencyRulesConfig(BaseModel):
    """
    Rules whose trigger forces the zone (and their own category) to CRITICAL regardless of
    the additive score. Policy: any rule keyed to a sensor's own "critical" band is
    emergency-eligible by design (critical H2S, LEL, smoke, pressure, temperature, oxygen),
    plus the emergency-shutdown flag — a direct reading of "never trigger on one parameter
    alone unless it represents an emergency condition." Compound/contextual rules (hot work +
    gas, lone worker, multiple equipment down, ...) are never emergency-eligible.

    Explicit frozenset, not derived by string-matching rule_ids — explicit beats implicit for
    something this safety-critical.
    """

    emergency_rule_ids: frozenset[str] = frozenset(
        {
            "RULE_H2S_CRITICAL",
            "RULE_OXYGEN_LOW_CRITICAL",
            "RULE_COMBUSTIBLE_GAS_CRITICAL",
            "RULE_SMOKE_CRITICAL",
            "RULE_PROCESS_TEMPERATURE_CRITICAL",
            "RULE_PROCESS_PRESSURE_CRITICAL",
            "RULE_EMERGENCY_SHUTDOWN_ACTIVE",
        }
    )


class RiskEngineConfig(BaseModel):
    severity_bands: SeverityBandsConfig = SeverityBandsConfig()
    confidence_bands: ConfidenceBandsConfig = ConfidenceBandsConfig()
    rule_weights: RuleWeightsConfig = RuleWeightsConfig()
    staleness: StalenessConfig = StalenessConfig()
    thresholds: ThresholdsConfig = ThresholdsConfig()
    emergency: EmergencyRulesConfig = EmergencyRulesConfig()
    explanation_top_n: int = 3
    recommended_actions_limit: int = 5
