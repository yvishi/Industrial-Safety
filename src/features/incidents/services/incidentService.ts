import { apiGet, apiPost } from '@/services/httpClient'
import type { Page } from '@/types/common'
import type { Incident, IncidentClassification, IncidentSeverity, IncidentStatus } from '../types/incident'
import { mapIncident } from './mappers'
import type { RawIncident, RawPage } from './wireTypes'

/** Incident list — filterable by zone, workflow status, and classification. */
export async function fetchIncidents(filters: {
  zoneId?: string
  status?: IncidentStatus
  classification?: IncidentClassification
  page?: number
  pageSize?: number
} = {}): Promise<Page<Incident>> {
  const params = new URLSearchParams()
  if (filters.zoneId !== undefined) params.set('zone_id', filters.zoneId)
  if (filters.status !== undefined) params.set('status', filters.status)
  if (filters.classification !== undefined) params.set('classification', filters.classification)
  if (filters.page !== undefined) params.set('page', String(filters.page))
  if (filters.pageSize !== undefined) params.set('page_size', String(filters.pageSize))

  const query = params.toString()
  const raw = await apiGet<RawPage<RawIncident>>(`/api/v1/incidents${query ? `?${query}` : ''}`)
  return {
    items: raw.items.map(mapIncident),
    total: raw.total,
    page: raw.page,
    pageSize: raw.page_size,
  }
}

export async function fetchIncident(incidentId: string): Promise<Incident> {
  const raw = await apiGet<RawIncident>(`/api/v1/incidents/${incidentId}`)
  return mapIncident(raw)
}

export async function createIncident(payload: {
  primaryZoneId: string
  title: string
  description: string
  classification?: IncidentClassification
  openedById?: string
}): Promise<Incident> {
  const raw = await apiPost<RawIncident>('/api/v1/incidents', {
    primary_zone_id: payload.primaryZoneId,
    title: payload.title,
    description: payload.description,
    ...(payload.classification !== undefined ? { classification: payload.classification } : {}),
    ...(payload.openedById !== undefined ? { opened_by_id: payload.openedById } : {}),
  })
  return mapIncident(raw)
}

export async function addIncidentNote(
  incidentId: string,
  payload: { noteText: string; actorId?: string },
): Promise<Incident> {
  const raw = await apiPost<RawIncident>(`/api/v1/incidents/${incidentId}/notes`, {
    note_text: payload.noteText,
    ...(payload.actorId !== undefined ? { actor_id: payload.actorId } : {}),
  })
  return mapIncident(raw)
}

export async function escalateIncident(
  incidentId: string,
  payload: { classification: IncidentClassification; actorId?: string },
): Promise<Incident> {
  const raw = await apiPost<RawIncident>(`/api/v1/incidents/${incidentId}/escalate`, {
    classification: payload.classification,
    ...(payload.actorId !== undefined ? { actor_id: payload.actorId } : {}),
  })
  return mapIncident(raw)
}

export async function closeIncident(
  incidentId: string,
  payload: {
    incidentSeverity?: IncidentSeverity
    rootCause?: string
    correctiveActions?: string[]
    actorId?: string
  } = {},
): Promise<Incident> {
  const raw = await apiPost<RawIncident>(`/api/v1/incidents/${incidentId}/close`, {
    ...(payload.incidentSeverity !== undefined ? { incident_severity: payload.incidentSeverity } : {}),
    ...(payload.rootCause !== undefined ? { root_cause: payload.rootCause } : {}),
    ...(payload.correctiveActions !== undefined
      ? { corrective_actions: payload.correctiveActions }
      : {}),
    ...(payload.actorId !== undefined ? { actor_id: payload.actorId } : {}),
  })
  return mapIncident(raw)
}
