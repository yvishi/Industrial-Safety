"""
Reports & Analytics schemas: read-only, cross-entity aggregation reports for supervisors and
compliance staff. Unlike schemas/risk.py or schemas/incident.py, nothing here is built from a
single ORM row (`ORMBase`/`from_attributes`) — every report is assembled by ReportingService
from several queries into a plain BaseModel, the same way PlantRiskSummary is hand-built in
services/risk.py rather than read off one model instance.

RiskCategory/TrendDirection are the engine's own taxonomy (app.risk_engine.config.schema) and
IncidentClassification is the Incident lifecycle's own taxonomy (app.schemas.incident) — both
reused directly here, never redefined, matching schemas/risk.py's own re-export convention.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.risk_engine.config.schema import RiskCategory, TrendDirection
from app.schemas.incident import IncidentClassification


class SafetyTrendPeriodPoint(BaseModel):
    period_start: datetime
    incidents_opened: int
    incidents_resolved: int
    normal_count: int
    low_count: int
    moderate_count: int
    high_count: int
    critical_count: int


class SafetyTrendReport(BaseModel):
    since: datetime
    until: datetime
    zone_id: UUID | None
    period_granularity: str  # "day" | "week" | "month"
    periods: list[SafetyTrendPeriodPoint]  # ascending by period_start
    total_incidents_opened: int
    total_incidents_resolved: int
    trend_direction: TrendDirection
    trend_summary: str


class ZoneHazardSummary(BaseModel):
    zone_id: UUID
    zone_name: str
    incident_count: int
    open_incident_count: int
    reportable_incident_count: int
    avg_risk_score: float | None
    top_category: RiskCategory | None


class HazardCategoryFrequency(BaseModel):
    category: RiskCategory
    trigger_count: int


class TriggeredRuleFrequency(BaseModel):
    rule_id: str
    category: RiskCategory
    description: str
    trigger_count: int


class ZoneHazardReport(BaseModel):
    since: datetime
    until: datetime
    zones: list[ZoneHazardSummary]  # sorted incident_count desc
    hazard_categories: list[HazardCategoryFrequency]  # sorted trigger_count desc
    top_rules: list[TriggeredRuleFrequency]  # top 10, sorted trigger_count desc


class ClassificationCount(BaseModel):
    classification: IncidentClassification
    count: int


class RecommendationTemplateFrequency(BaseModel):
    template_id: str
    title: str
    category: str
    trigger_count: int


class IncidentResponseReport(BaseModel):
    since: datetime
    until: datetime
    zone_id: UUID | None
    incidents_resolved_count: int
    incidents_closed_count: int
    mean_time_to_resolve_hours: float | None
    mean_time_to_close_hours: float | None
    recommendations_acknowledged_count: int
    mean_time_to_acknowledge_minutes: float | None
    classification_breakdown: list[ClassificationCount]
    top_recommendation_templates: list[RecommendationTemplateFrequency]  # top 10
