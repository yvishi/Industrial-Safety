/**
 * Raw shapes exactly as the backend's Pydantic schemas serialize them (snake_case).
 * Never imported outside this services/ folder — everything else in the app sees the
 * camelCase domain types from ../types, mapped below.
 */

export interface RawZone {
  id: string
  code: string
  name: string
  zone_type: string
  zone_category: string
  description: string | null
  grid_row: number | null
  grid_col: number | null
}

export interface RawPlant {
  id: string
  code: string
  name: string
  city: string | null
  region: string | null
  country: string | null
}

export interface RawWorker {
  id: string
  employee_id: string
  first_name: string
  last_name: string
  role: string
  shift: string | null
  current_zone_id: string | null
}

export interface RawEquipment {
  id: string
  tag_number: string
  name: string
  equipment_type: string
  status: string
  criticality: string | null
}

export interface RawSensor {
  id: string
  tag_number: string
  sensor_type: string
  unit_of_measure: string
  status: string
  normal_min: number | null
  normal_max: number | null
  warning_min: number | null
  warning_max: number | null
  critical_min: number | null
  critical_max: number | null
  sampling_interval_seconds: number
  last_value: number | null
  last_reading_at: string | null
}

export interface RawPermit {
  id: string
  zone_id: string
  permit_number: string
  permit_type: string
  required_isolation: string | null
  status: string
  description: string | null
  valid_from: string | null
  valid_until: string | null
}

export interface RawEvent {
  id: string
  event_type: string
  title: string
  description: string | null
  occurred_at: string
  zone_id: string | null
}

export interface RawZoneState {
  zone: RawZone
  workers: RawWorker[]
  equipment: RawEquipment[]
  sensors: RawSensor[]
  active_permit_count: number
}

export interface RawPlantState {
  plant: RawPlant
  generated_at: string
  zones: RawZoneState[]
  active_permits: RawPermit[]
  recent_events: RawEvent[]
}

export interface RawPage<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface RawRiskEntityRef {
  entity_type: string
  entity_id: string
  label: string
}

export interface RawRiskContributor {
  rule_id: string
  category: string
  factor: string
  impact: number
  severity: string
  rationale: string
  source_refs: RawRiskEntityRef[]
}

export interface RawRecommendedAction {
  rule_id: string
  action: string
  priority: string
}

export interface RawCategoryRisk {
  category: string
  score: number
  level: string
  top_contributor: string | null
}

export interface RawRiskAssessment {
  zone_id: string
  zone_name: string
  engine_version: string
  score: number
  level: string
  is_emergency_override: boolean
  confidence_score: number
  confidence_label: string
  categories: RawCategoryRisk[]
  contributors: RawRiskContributor[]
  recommended_actions: RawRecommendedAction[]
  previous_score: number | null
  score_delta: number | null
  trend_direction: string | null
  explanation: string
  triggered_rules: string[]
  evaluated_at: string
}

export interface RawPlantRiskSummary {
  generated_at: string
  zones: RawRiskAssessment[]
  highest_risk_zone_id: string | null
  plant_wide_emergency_active: boolean
}

export interface RawRecommendation {
  id: string
  zone_id: string
  zone_name: string
  template_id: string
  category: string
  priority: string
  state: string
  title: string
  action_text: string
  expected_outcomes: string[]
  rationale: string
  source_rule_ids: string[]
  target_entity: RawRiskEntityRef
  engine_version: string
  first_generated_at: string
  last_seen_at: string
  acknowledged_at: string | null
  resolved_at: string | null
}

export interface RawPlantRecommendationSummary {
  generated_at: string
  top_recommendations: RawRecommendation[]
  counts_by_priority: Record<string, number>
  plant_wide_emergency_active: boolean
}
