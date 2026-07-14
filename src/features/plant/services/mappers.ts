import type { Equipment, EquipmentStatus, EquipmentType } from '../types/equipment'
import type { PlantEvent } from '../types/event'
import type { PlantProfile } from '../types/plant'
import type { Permit, PermitStatus, PermitType } from '../types/permit'
import type { PlantRecommendationSummary, Recommendation, RecommendationPriority, RecommendationState } from '../types/recommendation'
import type {
  CategoryRisk,
  ConfidenceLevel,
  PlantRiskSummary,
  RecommendedAction,
  RiskAssessment,
  RiskCategoryKey,
  RiskContributor,
  RiskEntityRef,
  RiskLevel,
  TrendDirection,
} from '../types/risk'
import type { Sensor, SensorStatus, SensorType } from '../types/sensor'
import type { Shift, Worker, WorkerRole } from '../types/worker'
import type { Zone, ZoneCategory, ZoneType } from '../types/zone'
import type {
  RawCategoryRisk,
  RawEquipment,
  RawEvent,
  RawPermit,
  RawPlant,
  RawPlantRecommendationSummary,
  RawPlantRiskSummary,
  RawRecommendation,
  RawRecommendedAction,
  RawRiskAssessment,
  RawRiskContributor,
  RawRiskEntityRef,
  RawSensor,
  RawWorker,
  RawZone,
} from './wireTypes'

export function mapPlant(raw: RawPlant): PlantProfile {
  return {
    name: raw.name,
    code: raw.code,
    location: [raw.city, raw.region].filter(Boolean).join(', ') || (raw.country ?? ''),
  }
}

export function mapZone(raw: RawZone): Zone {
  return {
    id: raw.id,
    code: raw.code,
    name: raw.name,
    zoneType: raw.zone_type as ZoneType,
    zoneCategory: raw.zone_category as ZoneCategory,
    description: raw.description,
    gridPosition: { row: raw.grid_row ?? 0, col: raw.grid_col ?? 0 },
  }
}

export function mapWorker(raw: RawWorker): Worker {
  return {
    id: raw.id,
    employeeId: raw.employee_id,
    firstName: raw.first_name,
    lastName: raw.last_name,
    role: raw.role as WorkerRole,
    shift: raw.shift as Shift | null,
    currentZoneId: raw.current_zone_id,
  }
}

export function mapEquipment(raw: RawEquipment): Equipment {
  return {
    id: raw.id,
    tagNumber: raw.tag_number,
    name: raw.name,
    equipmentType: raw.equipment_type as EquipmentType,
    status: raw.status as EquipmentStatus,
    criticality: raw.criticality,
  }
}

export function mapSensor(raw: RawSensor): Sensor {
  return {
    id: raw.id,
    tagNumber: raw.tag_number,
    sensorType: raw.sensor_type as SensorType,
    unitOfMeasure: raw.unit_of_measure,
    status: raw.status as SensorStatus,
    normalMin: raw.normal_min,
    normalMax: raw.normal_max,
    warningMin: raw.warning_min,
    warningMax: raw.warning_max,
    criticalMin: raw.critical_min,
    criticalMax: raw.critical_max,
    samplingIntervalSeconds: raw.sampling_interval_seconds,
    lastValue: raw.last_value,
    lastReadingAt: raw.last_reading_at,
  }
}

export function mapPermit(raw: RawPermit): Permit {
  return {
    id: raw.id,
    zoneId: raw.zone_id,
    permitNumber: raw.permit_number,
    permitType: raw.permit_type as PermitType,
    requiredIsolation: raw.required_isolation,
    status: raw.status as PermitStatus,
    description: raw.description,
    validFrom: raw.valid_from,
    validUntil: raw.valid_until,
  }
}

export function mapEvent(raw: RawEvent): PlantEvent {
  return {
    id: raw.id,
    eventType: raw.event_type,
    title: raw.title,
    description: raw.description,
    occurredAt: raw.occurred_at,
    zoneId: raw.zone_id,
  }
}

function mapRiskEntityRef(raw: RawRiskEntityRef): RiskEntityRef {
  return { entityType: raw.entity_type, entityId: raw.entity_id, label: raw.label }
}

function mapRiskContributor(raw: RawRiskContributor): RiskContributor {
  return {
    ruleId: raw.rule_id,
    category: raw.category as RiskCategoryKey,
    factor: raw.factor,
    impact: raw.impact,
    severity: raw.severity,
    rationale: raw.rationale,
    sourceRefs: raw.source_refs.map(mapRiskEntityRef),
  }
}

function mapRecommendedAction(raw: RawRecommendedAction): RecommendedAction {
  return { ruleId: raw.rule_id, action: raw.action, priority: raw.priority }
}

function mapCategoryRisk(raw: RawCategoryRisk): CategoryRisk {
  return {
    category: raw.category as RiskCategoryKey,
    score: raw.score,
    level: raw.level as RiskLevel,
    topContributor: raw.top_contributor,
  }
}

export function mapRiskAssessment(raw: RawRiskAssessment): RiskAssessment {
  return {
    zoneId: raw.zone_id,
    zoneName: raw.zone_name,
    engineVersion: raw.engine_version,
    score: raw.score,
    level: raw.level as RiskLevel,
    isEmergencyOverride: raw.is_emergency_override,
    confidenceScore: raw.confidence_score,
    confidenceLabel: raw.confidence_label as ConfidenceLevel,
    categories: raw.categories.map(mapCategoryRisk),
    contributors: raw.contributors.map(mapRiskContributor),
    recommendedActions: raw.recommended_actions.map(mapRecommendedAction),
    previousScore: raw.previous_score,
    scoreDelta: raw.score_delta,
    trendDirection: raw.trend_direction as TrendDirection | null,
    explanation: raw.explanation,
    triggeredRules: raw.triggered_rules,
    evaluatedAt: raw.evaluated_at,
  }
}

export function mapPlantRiskSummary(raw: RawPlantRiskSummary): PlantRiskSummary {
  return {
    generatedAt: raw.generated_at,
    zones: raw.zones.map(mapRiskAssessment),
    highestRiskZoneId: raw.highest_risk_zone_id,
    plantWideEmergencyActive: raw.plant_wide_emergency_active,
  }
}

export function mapRecommendation(raw: RawRecommendation): Recommendation {
  return {
    id: raw.id,
    zoneId: raw.zone_id,
    zoneName: raw.zone_name,
    templateId: raw.template_id,
    category: raw.category as RiskCategoryKey,
    priority: raw.priority as RecommendationPriority,
    state: raw.state as RecommendationState,
    title: raw.title,
    actionText: raw.action_text,
    expectedOutcomes: raw.expected_outcomes,
    rationale: raw.rationale,
    sourceRuleIds: raw.source_rule_ids,
    targetEntity: mapRiskEntityRef(raw.target_entity),
    engineVersion: raw.engine_version,
    firstGeneratedAt: raw.first_generated_at,
    lastSeenAt: raw.last_seen_at,
    acknowledgedAt: raw.acknowledged_at,
    resolvedAt: raw.resolved_at,
  }
}

export function mapPlantRecommendationSummary(raw: RawPlantRecommendationSummary): PlantRecommendationSummary {
  return {
    generatedAt: raw.generated_at,
    topRecommendations: raw.top_recommendations.map(mapRecommendation),
    countsByPriority: raw.counts_by_priority as PlantRecommendationSummary['countsByPriority'],
    plantWideEmergencyActive: raw.plant_wide_emergency_active,
  }
}
