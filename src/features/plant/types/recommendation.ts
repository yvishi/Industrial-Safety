import type { RiskCategoryKey, RiskEntityRef } from './risk'

export type RecommendationPriority = 'critical' | 'high' | 'moderate' | 'low'

/** v1 has no "dismissed" state — an operator who chooses not to act acknowledges instead; the
 * recommendation stays visible until the underlying condition actually clears. */
export type RecommendationState = 'new' | 'acknowledged' | 'resolved'

/** Live Recommendation Engine output for one zone — mirrors GET /api/v1/recommendations/zones/{id}. */
export interface Recommendation {
  id: string
  zoneId: string
  zoneName: string
  incidentId: string | null
  templateId: string
  category: RiskCategoryKey
  priority: RecommendationPriority
  state: RecommendationState
  title: string
  actionText: string
  expectedOutcomes: string[]
  rationale: string
  sourceRuleIds: string[]
  targetEntity: RiskEntityRef
  engineVersion: string
  firstGeneratedAt: string
  lastSeenAt: string
  acknowledgedAt: string | null
  resolvedAt: string | null
}

/** Plant-wide Action Queue — mirrors GET /api/v1/recommendations/plant. */
export interface PlantRecommendationSummary {
  generatedAt: string
  topRecommendations: Recommendation[]
  countsByPriority: Partial<Record<RecommendationPriority, number>>
  plantWideEmergencyActive: boolean
}
