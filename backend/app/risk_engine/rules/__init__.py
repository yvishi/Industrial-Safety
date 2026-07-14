"""Aggregates every concrete rule into a single ALL_RULES list the engine iterates over."""

from app.risk_engine.rules import (
    equipment,
    fire_explosion,
    gas_hazard,
    permit_compliance,
    personnel_exposure,
    process_safety,
)
from app.risk_engine.rules.base import Rule, RuleResult

ALL_RULES: list[Rule] = (
    gas_hazard.RULES
    + fire_explosion.RULES
    + equipment.RULES
    + personnel_exposure.RULES
    + permit_compliance.RULES
    + process_safety.RULES
)

__all__ = ["ALL_RULES", "Rule", "RuleResult"]
