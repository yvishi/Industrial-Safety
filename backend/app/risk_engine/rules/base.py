"""
Rule contract. Every rule is a small, independent class that reads a ZoneFacts snapshot and
returns exactly one RuleResult. Rules never see each other's output and never call each other
— even "compound" rules (e.g. hot work permit + elevated gas) just check multiple conditions
on the same ZoneFacts in one evaluate() body. This is what lets a new rule be added as a new
file without touching any existing rule, and lets every rule be unit-tested in isolation with
a hand-built ZoneFacts fixture and no mocking.

Weight (impact) and emergency-override membership are both looked up from RiskEngineConfig at
evaluation time, never hardcoded on the rule class — config-driven, not magic numbers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import ClassVar

from app.risk_engine.config.schema import RiskCategory, RiskEngineConfig
from app.risk_engine.facts import EntityRef, ZoneFacts


@dataclass(frozen=True)
class RuleResult:
    rule_id: str
    triggered: bool
    category: RiskCategory
    factor: str  # short label, e.g. "H2S concentration"
    impact: int  # 0 when not triggered
    severity: str  # "info"|"low"|"moderate"|"high"|"critical"; "info" when not triggered
    rationale: str  # fully-formed sentence fragment with real values interpolated; "" when not triggered
    is_emergency_override: bool = False
    referenced_entities: tuple[EntityRef, ...] = field(default_factory=tuple)
    suggested_action: str | None = None


class Rule(ABC):
    rule_id: ClassVar[str]
    category: ClassVar[RiskCategory]
    default_severity: ClassVar[str]
    description: ClassVar[str]
    suggested_action: ClassVar[str | None] = None

    @abstractmethod
    def evaluate(self, facts: ZoneFacts, config: RiskEngineConfig) -> RuleResult: ...

    def _result(
        self,
        *,
        triggered: bool,
        factor: str,
        rationale: str,
        config: RiskEngineConfig,
        referenced_entities: tuple[EntityRef, ...] = (),
    ) -> RuleResult:
        """Shared boilerplate every concrete rule calls at the end of evaluate()."""
        impact = config.rule_weights.weights.get(self.rule_id, 0) if triggered else 0
        return RuleResult(
            rule_id=self.rule_id,
            triggered=triggered,
            category=self.category,
            factor=factor,
            impact=impact,
            severity=self.default_severity if triggered else "info",
            rationale=rationale if triggered else "",
            is_emergency_override=self.rule_id in config.emergency.emergency_rule_ids,
            referenced_entities=referenced_entities if triggered else (),
            suggested_action=self.suggested_action if triggered else None,
        )
