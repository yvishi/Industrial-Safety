import { apiGet } from '@/services/httpClient'
import type { Page } from '@/types/common'
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

/** General-purpose event lookup — e.g. the Events feed for one Incident's timeline. */
export async function fetchEvents(filters: {
  zoneId?: string
  incidentId?: string
  page?: number
  pageSize?: number
} = {}): Promise<Page<PlantEvent>> {
  const params = new URLSearchParams()
  if (filters.zoneId !== undefined) params.set('zone_id', filters.zoneId)
  if (filters.incidentId !== undefined) params.set('incident_id', filters.incidentId)
  if (filters.page !== undefined) params.set('page', String(filters.page))
  if (filters.pageSize !== undefined) params.set('page_size', String(filters.pageSize))

  const query = params.toString()
  const raw = await apiGet<RawPage<RawEvent>>(`/api/v1/events${query ? `?${query}` : ''}`)
  return {
    items: raw.items.map(mapEvent),
    total: raw.total,
    page: raw.page,
    pageSize: raw.page_size,
  }
}
