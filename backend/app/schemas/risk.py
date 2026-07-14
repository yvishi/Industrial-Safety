from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, computed_field

from app.risk_engine.config.schema import ConfidenceLevel, RiskCategory, RiskLevel, TrendDirection
from app.schemas.common import TimestampedRead

__all__ = [
    "ConfidenceLevel",
    "RiskCategory",
    "RiskLevel",
    "TrendDirection",
    "EntityRefRead",
    "RiskContributor",
    "RecommendedAction",
    "CategoryRisk",
    "RiskAssessment",
    "PlantRiskSummary",
    "RiskSnapshotRead",
    "RuleCatalogEntry",
]


class EntityRefRead(BaseModel):
    entity_type: str
    entity_id: UUID
    label: str


class RiskContributor(BaseModel):
    rule_id: str
    category: RiskCategory
    factor: str
    impact: int
    severity: str
    rationale: str
    source_refs: list[EntityRefRead] = []


class RecommendedAction(BaseModel):
    rule_id: str
    action: str
    priority: str


class CategoryRisk(BaseModel):
    category: RiskCategory
    score: int
    level: RiskLevel
    top_contributor: str | None = None


class RiskAssessment(BaseModel):
    """
    Live-computed, on-demand risk assessment for one zone (never persisted itself — see
    RiskSnapshotRead for the frozen, persisted counterpart). score/level/categories/
    contributors/explanation/confidence_score/confidence_label/engine_version are the facts
    the engine produced for THIS evaluation; previous_score/score_delta/trend_direction are
    computed by comparing against the last persisted RiskSnapshot for this zone (None if none
    exists yet).
    """

    zone_id: UUID
    zone_name: str
    engine_version: str
    score: int
    level: RiskLevel
    is_emergency_override: bool
    confidence_score: int
    confidence_label: ConfidenceLevel
    categories: list[CategoryRisk]
    contributors: list[RiskContributor]
    recommended_actions: list[RecommendedAction]
    previous_score: int | None = None
    score_delta: int | None = None
    trend_direction: TrendDirection | None = None
    evaluation_duration_ms: int
    explanation: str
    evaluated_at: datetime

    @computed_field
    @property
    def triggered_rules(self) -> list[str]:
        return [c.rule_id for c in self.contributors]


class PlantRiskSummary(BaseModel):
    generated_at: datetime
    zones: list[RiskAssessment]
    highest_risk_zone_id: UUID | None
    plant_wide_emergency_active: bool


class RiskSnapshotRead(TimestampedRead):
    """A frozen, persisted assessment (see models.risk_snapshot.RiskSnapshot). Only written
    when a zone's level changed or its score moved significantly — every row is, by
    construction, a meaningful change. previous_score/score_delta/trend_direction are computed
    at read time against the prior row in zone_id order, not stored."""

    zone_id: UUID
    score: int
    level: RiskLevel
    confidence_score: int
    confidence_label: ConfidenceLevel
    is_emergency_override: bool
    categories: list[CategoryRisk]
    contributors: list[RiskContributor]
    explanation: str
    engine_version: str
    trigger_source: str
    evaluation_duration_ms: int
    evaluated_at: datetime
    previous_score: int | None = None
    score_delta: int | None = None
    trend_direction: TrendDirection | None = None

    @computed_field
    @property
    def triggered_rules(self) -> list[str]:
        return [c.rule_id for c in self.contributors]


class RuleCatalogEntry(BaseModel):
    """Static catalog entry for GET /api/v1/risk/rules — introspected from config, no DB."""

    rule_id: str
    category: RiskCategory
    description: str
    default_severity: str
    weight: int
    is_emergency_override: bool
    suggested_action: str | None = None
