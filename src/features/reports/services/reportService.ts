import { apiGet } from '@/services/httpClient'
import type { IncidentResponseReport, SafetyTrendReport, ZoneHazardReport } from '../types/reports'
import { mapIncidentResponseReport, mapSafetyTrendReport, mapZoneHazardReport } from './mappers'
import type { RawIncidentResponseReport, RawSafetyTrendReport, RawZoneHazardReport } from './wireTypes'

export interface ReportFilters {
  since?: string
  until?: string
  zoneId?: string
}

function buildQuery(filters: ReportFilters): string {
  const params = new URLSearchParams()
  if (filters.since !== undefined) params.set('since', filters.since)
  if (filters.until !== undefined) params.set('until', filters.until)
  if (filters.zoneId !== undefined) params.set('zone_id', filters.zoneId)
  const query = params.toString()
  return query ? `?${query}` : ''
}

/** Trend of incident volume and risk-level mix over time — "is the refinery becoming safer?" */
export async function fetchSafetyTrend(filters: ReportFilters = {}): Promise<SafetyTrendReport> {
  const raw = await apiGet<RawSafetyTrendReport>(
    `/api/v1/reports/safety-trend${buildQuery(filters)}`,
  )
  return mapSafetyTrendReport(raw)
}

/** Cross-zone hazard comparison — no zone_id filter, this report IS the comparison. */
export async function fetchZoneHazardReport(
  filters: Omit<ReportFilters, 'zoneId'> = {},
): Promise<ZoneHazardReport> {
  const raw = await apiGet<RawZoneHazardReport>(
    `/api/v1/reports/zones-hazards${buildQuery(filters)}`,
  )
  return mapZoneHazardReport(raw)
}

/** Incident resolution and recommendation-acknowledgement timing. */
export async function fetchIncidentResponse(
  filters: ReportFilters = {},
): Promise<IncidentResponseReport> {
  const raw = await apiGet<RawIncidentResponseReport>(
    `/api/v1/reports/incident-response${buildQuery(filters)}`,
  )
  return mapIncidentResponseReport(raw)
}
