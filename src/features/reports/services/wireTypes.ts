/**
 * Raw shapes exactly as the backend's Pydantic schemas serialize them (snake_case).
 * Never imported outside this services/ folder — everything else in the app sees the
 * camelCase domain types from ../types, mapped below.
 */

export interface RawSafetyTrendPeriod {
  period_start: string
  incidents_opened: number
  incidents_resolved: number
  normal_count: number
  low_count: number
  moderate_count: number
  high_count: number
  critical_count: number
}

export interface RawSafetyTrendReport {
  since: string | null
  until: string | null
  zone_id: string | null
  period_granularity: string
  periods: RawSafetyTrendPeriod[]
  total_incidents_opened: number
  total_incidents_resolved: number
  trend_direction: string
  trend_summary: string
}

export interface RawZoneHazardSummary {
  zone_id: string
  zone_name: string
  incident_count: number
  open_incident_count: number
  reportable_incident_count: number
  avg_risk_score: number | null
  top_category: string | null
}

export interface RawHazardCategoryCount {
  category: string
  trigger_count: number
}

export interface RawTopRule {
  rule_id: string
  category: string
  description: string
  trigger_count: number
}

export interface RawZoneHazardReport {
  since: string | null
  until: string | null
  zones: RawZoneHazardSummary[]
  hazard_categories: RawHazardCategoryCount[]
  top_rules: RawTopRule[]
}

export interface RawClassificationCount {
  classification: string
  count: number
}

export interface RawRecommendationTemplateCount {
  template_id: string
  title: string
  category: string
  trigger_count: number
}

export interface RawIncidentResponseReport {
  since: string | null
  until: string | null
  zone_id: string | null
  incidents_resolved_count: number
  incidents_closed_count: number
  mean_time_to_resolve_hours: number | null
  mean_time_to_close_hours: number | null
  recommendations_acknowledged_count: number
  mean_time_to_acknowledge_minutes: number | null
  classification_breakdown: RawClassificationCount[]
  top_recommendation_templates: RawRecommendationTemplateCount[]
}
