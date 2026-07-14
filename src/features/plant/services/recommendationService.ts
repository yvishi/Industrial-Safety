import { apiGet, apiPost } from '@/services/httpClient'
import type { PlantRecommendationSummary, Recommendation } from '../types/recommendation'
import { mapPlantRecommendationSummary, mapRecommendation } from './mappers'
import type { RawPlantRecommendationSummary, RawRecommendation } from './wireTypes'

/** Active recommendations for one zone, priority-sorted. */
export async function fetchZoneRecommendations(zoneId: string): Promise<Recommendation[]> {
  const raw = await apiGet<RawRecommendation[]>(`/api/v1/recommendations/zones/${zoneId}`)
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
