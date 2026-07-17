import { apiGet, apiPost } from '@/services/httpClient'
import type { PlantRecommendationSummary, Recommendation } from '../types/recommendation'
import { mapPlantRecommendationSummary, mapRecommendation } from './mappers'
import type { RawPlantRecommendationSummary, RawRecommendation } from './wireTypes'

/** Recommendations for one zone, priority-sorted — active only by default; pass
 * `includeResolved` to also see ones that have already cleared (e.g. for a closed incident's
 * own history, which can legitimately reference a recommendation that resolved before it did). */
export async function fetchZoneRecommendations(zoneId: string, includeResolved = false): Promise<Recommendation[]> {
  const query = includeResolved ? '?include_resolved=true' : ''
  const raw = await apiGet<RawRecommendation[]>(`/api/v1/recommendations/zones/${zoneId}${query}`)
  return raw.map(mapRecommendation)
}

/** Cross-zone Action Queue — the top priority-ranked recommendations plant-wide. */
export async function fetchPlantRecommendations(): Promise<PlantRecommendationSummary> {
  const raw = await apiGet<RawPlantRecommendationSummary>('/api/v1/recommendations/plant')
  return mapPlantRecommendationSummary(raw)
}

export async function acknowledgeRecommendation(recommendationId: string): Promise<Recommendation> {
  const raw = await apiPost<RawRecommendation>(`/api/v1/recommendations/${recommendationId}/acknowledge`)
  return mapRecommendation(raw)
}

export async function resolveRecommendation(recommendationId: string): Promise<Recommendation> {
  const raw = await apiPost<RawRecommendation>(`/api/v1/recommendations/${recommendationId}/resolve`)
  return mapRecommendation(raw)
}
