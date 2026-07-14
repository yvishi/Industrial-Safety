from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel

from app.risk_engine.config.schema import RiskCategory
from app.schemas.common import TimestampedRead
from app.schemas.risk import EntityRefRead


class RecommendationPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"


class RecommendationState(str, Enum):
    """v1 has three states only — no DISMISSED. An operator who chooses not to act
    acknowledges instead; the recommendation stays visible until the condition actually
    clears (auto-resolved) or the operator marks it resolved."""

    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class RecommendationRead(TimestampedRead):
    zone_id: UUID
    zone_name: str
    template_id: str
    category: RiskCategory
    priority: RecommendationPriority
    state: RecommendationState
    title: str
    action_text: str
    expected_outcomes: list[str]
    rationale: str
    source_rule_ids: list[str]
    target_entity: EntityRefRead
    engine_version: str
    generation_source: str
    first_generated_at: datetime
    last_seen_at: datetime
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None


class PlantRecommendationSummary(BaseModel):
    generated_at: datetime
    top_recommendations: list[RecommendationRead]
    counts_by_priority: dict[str, int]
    plant_wide_emergency_active: bool


class RecommendationTemplateEntry(BaseModel):
    """GET /api/v1/recommendations/templates — static catalog, no DB, mirrors RuleCatalogEntry."""

    template_id: str
    category: RiskCategory
    title: str
    action_text: str
    expected_outcomes: list[str]
    target_entity_type: str
    source_rule_ids: list[str]
