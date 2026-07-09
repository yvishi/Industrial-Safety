import { apiGet } from '@/services/httpClient'
import type { PlantEvent } from '../types/event'
import type { PlantState, ZoneState } from '../types/state'
import {
  mapEquipment,
  mapEvent,
  mapPermit,
  mapPlant,
  mapSensor,
  mapWorker,
  mapZone,
} from './mappers'
import type { RawEvent, RawPage, RawPlantState, RawZoneState } from './wireTypes'

function mapZoneState(raw: RawZoneState): ZoneState {
  return {
    zone: mapZone(raw.zone),
    workers: raw.workers.map(mapWorker),
    equipment: raw.equipment.map(mapEquipment),
    sensors: raw.sensors.map(mapSensor),
    activePermitCount: raw.active_permit_count,
  }
}

/** The single call the Plant module polls: everything needed to render the whole plant. */
export async function fetchPlantState(): Promise<PlantState> {
  const raw = await apiGet<RawPlantState>('/api/v1/state')
  return {
    plant: mapPlant(raw.plant),
    generatedAt: raw.generated_at,
    zones: raw.zones.map(mapZoneState),
    activePermits: raw.active_permits.map(mapPermit),
    recentEvents: raw.recent_events.map(mapEvent),
  }
}

/** Recent activity for one zone — the /state snapshot only carries a plant-wide slice. */
export async function fetchZoneEvents(zoneId: string, limit = 10): Promise<PlantEvent[]> {
  const raw = await apiGet<RawPage<RawEvent>>(
    `/api/v1/events?zone_id=${zoneId}&page_size=${limit}`,
  )
  return raw.items.map(mapEvent)
}
