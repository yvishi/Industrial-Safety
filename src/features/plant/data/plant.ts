import type { PlantProfile } from '../types/plant'

/**
 * Static site identity for Phase 1 — structural facts about the plant, not operational state.
 * Swap this for a real service call once a backend exists; the function signature stays the same.
 */
const PLANT_PROFILE: PlantProfile = {
  name: 'Riverbend Processing Facility',
  code: 'RPF-01',
  location: 'Riverbend, TX',
}

export function getPlantProfile(): PlantProfile {
  return PLANT_PROFILE
}
