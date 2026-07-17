import type { RiskCategoryKey, TrendDirection } from '@/features/plant/types/risk'
import type { IncidentClassification } from '@/features/incidents/types/incident'

export type PeriodGranularity = 'day' | 'week' | 'month'

export interface SafetyTrendPeriod {
  periodStart: string
  incidentsOpened: number
  incidentsResolved: number
  normalCount: number
  lowCount: number
  moderateCount: number
  highCount: number
  criticalCount: number
}

/** Mirrors GET /api/v1/reports/safety-trend — "is the refinery becoming safer?" */
export interface SafetyTrendReport {
  since: string | null
  until: string | null
  zoneId: string | null
  periodGranularity: PeriodGranularity
  periods: SafetyTrendPeriod[]
  totalIncidentsOpened: number
  totalIncidentsResolved: number
  trendDirection: TrendDirection
  trendSummary: string
}

export interface ZoneHazardSummary {
  zoneId: string
  zoneName: string
  incidentCount: number
  openIncidentCount: number
  reportableIncidentCount: number
  avgRiskScore: number | null
  topCategory: RiskCategoryKey | null
}

export interface HazardCategoryCount {
  category: RiskCategoryKey
  triggerCount: number
}

export interface TopRule {
  ruleId: string
  category: RiskCategoryKey
  description: string
  triggerCount: number
}

/** Mirrors GET /api/v1/reports/zones-hazards — "which zones/hazards need attention?" */
export interface ZoneHazardReport {
  since: string | null
  until: string | null
  zones: ZoneHazardSummary[]
  hazardCategories: HazardCategoryCount[]
  topRules: TopRule[]
}

export interface ClassificationCount {
  classification: IncidentClassification
  count: number
}

export interface RecommendationTemplateCount {
  templateId: string
  title: string
  category: RiskCategoryKey
  triggerCount: number
}

/** Mirrors GET /api/v1/reports/incident-response — "how fast do we resolve incidents /
 * act on recommendations?" */
export interface IncidentResponseReport {
  since: string | null
  until: string | null
  zoneId: string | null
  incidentsResolvedCount: number
  incidentsClosedCount: number
  meanTimeToResolveHours: number | null
  meanTimeToCloseHours: number | null
  recommendationsAcknowledgedCount: number
  meanTimeToAcknowledgeMinutes: number | null
  classificationBreakdown: ClassificationCount[]
  topRecommendationTemplates: RecommendationTemplateCount[]
}
