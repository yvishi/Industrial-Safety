/** Mirrors the backend's RiskCategory union (app/risk_engine/config/schema.py). */
export type RiskCategoryKey =
  | 'gas_hazard'
  | 'fire_explosion'
  | 'equipment'
  | 'personnel_exposure'
  | 'permit_compliance'
  | 'environmental'
  | 'process_safety'

export type RiskLevel = 'normal' | 'low' | 'moderate' | 'high' | 'critical'
export type ConfidenceLevel = 'high' | 'medium' | 'low'
export type TrendDirection = 'up' | 'down' | 'flat'

export interface RiskEntityRef {
  entityType: string
  entityId: string
  label: string
}

export interface RiskContributor {
  ruleId: string
  category: RiskCategoryKey
  factor: string
  impact: number
  severity: string
  rationale: string
  sourceRefs: RiskEntityRef[]
}

export interface RecommendedAction {
  ruleId: string
  action: string
  priority: string
}

export interface CategoryRisk {
  category: RiskCategoryKey
  score: number
  level: RiskLevel
  topContributor: string | null
}

/** Live-computed Compound Risk Engine assessment for one zone — mirrors GET /api/v1/risk/zones/{id}. */
export interface RiskAssessment {
  zoneId: string
  zoneName: string
  engineVersion: string
  score: number
  level: RiskLevel
  isEmergencyOverride: boolean
  confidenceScore: number
  confidenceLabel: ConfidenceLevel
  categories: CategoryRisk[]
  contributors: RiskContributor[]
  recommendedActions: RecommendedAction[]
  previousScore: number | null
  scoreDelta: number | null
  trendDirection: TrendDirection | null
  explanation: string
  triggeredRules: string[]
  evaluatedAt: string
}

/** Plant-wide risk rollup — mirrors GET /api/v1/risk/plant. */
export interface PlantRiskSummary {
  generatedAt: string
  zones: RiskAssessment[]
  highestRiskZoneId: string | null
  plantWideEmergencyActive: boolean
}
