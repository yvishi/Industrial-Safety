"""Equipment-state rules: safety-critical gear in maintenance, multiple assets down, and
maintenance activity lacking a permit-to-work."""

from app.risk_engine.config.schema import RiskCategory, RiskEngineConfig
from app.risk_engine.facts import EntityRef, ZoneFacts
from app.risk_engine.rules.base import Rule, RuleResult


class RuleSafetyCriticalUnderMaintenance(Rule):
    rule_id = "RULE_SAFETY_CRITICAL_UNDER_MAINTENANCE"
    category = RiskCategory.EQUIPMENT
    default_severity = "high"
    description = "Detects safety-critical equipment that is currently under maintenance."

    def evaluate(self, facts: ZoneFacts, config: RiskEngineConfig) -> RuleResult:
        matches = [
            e
            for e in facts.equipment
            if e.criticality == "safety_critical" and e.status == "under_maintenance"
        ]
        rationale = (
            f"{matches[0].tag_number} ({matches[0].equipment_type}) is safety-critical and "
            f"currently under maintenance."
            if matches
            else ""
        )
        return self._result(
            triggered=bool(matches),
            factor="Safety-Critical Equipment in Maintenance",
            rationale=rationale,
            config=config,
            referenced_entities=tuple(
                EntityRef("equipment", e.equipment_id, e.tag_number) for e in matches
            ),
        )


class RuleMultipleEquipmentDown(Rule):
    rule_id = "RULE_MULTIPLE_EQUIPMENT_DOWN"
    category = RiskCategory.EQUIPMENT
    default_severity = "moderate"
    description = "Detects when several pieces of equipment in the zone are out of service at once."

    def evaluate(self, facts: ZoneFacts, config: RiskEngineConfig) -> RuleResult:
        down = [e for e in facts.equipment if e.status in ("under_maintenance", "decommissioned")]
        triggered = len(down) >= config.thresholds.multiple_equipment_down_threshold
        rationale = (
            f"{len(down)} pieces of equipment in {facts.zone_name} are under maintenance or "
            f"decommissioned."
            if triggered
            else ""
        )
        return self._result(
            triggered=triggered,
            factor="Multiple Equipment Down",
            rationale=rationale,
            config=config,
            referenced_entities=tuple(
                EntityRef("equipment", e.equipment_id, e.tag_number) for e in down
            ),
        )


class RuleMaintenanceWithoutActivePermit(Rule):
    rule_id = "RULE_MAINTENANCE_WITHOUT_ACTIVE_PERMIT"
    category = RiskCategory.EQUIPMENT
    default_severity = "high"
    description = "Detects equipment under maintenance with no active permit-to-work covering it."
    suggested_action = "Verify a permit-to-work has been issued and approved for this maintenance activity."

    def evaluate(self, facts: ZoneFacts, config: RiskEngineConfig) -> RuleResult:
        matches = [
            e
            for e in facts.equipment
            if e.status == "under_maintenance"
            and not facts.active_permits_for_equipment(e.equipment_id)
        ]
        rationale = (
            f"{matches[0].tag_number} is under maintenance with no active permit-to-work on record."
            if matches
            else ""
        )
        return self._result(
            triggered=bool(matches),
            factor="Maintenance Without Active Permit",
            rationale=rationale,
            config=config,
            referenced_entities=tuple(
                EntityRef("equipment", e.equipment_id, e.tag_number) for e in matches
            ),
        )


RULES: list[Rule] = [
    RuleSafetyCriticalUnderMaintenance(),
    RuleMultipleEquipmentDown(),
    RuleMaintenanceWithoutActivePermit(),
]
