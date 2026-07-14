import { apiGet } from '@/services/httpClient'
import type { PlantRiskSummary } from '../types/risk'
import { mapPlantRiskSummary } from './mappers'
import type { RawPlantRiskSummary } from './wireTypes'

/** Live Compound Risk Engine assessment for every zone, one call — mirrors fetchPlantState. */
export async function fetchPlantRisk(): Promise<PlantRiskSummary> {
  const raw = await apiGet<RawPlantRiskSummary>('/api/v1/risk/plant')
  return mapPlantRiskSummary(raw)
}
