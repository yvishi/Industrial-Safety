import type { RiskLevel } from '@/features/plant/types/risk'

export type IncidentStatus = 'open' | 'resolved' | 'closed'
export type IncidentOrigin = 'system_detected' | 'manual'
export type IncidentClassification =
  | 'operational_episode'
  | 'near_miss'
  | 'safety_incident'
  | 'reportable_incident'
export type IncidentSeverity = 'negligible' | 'minor' | 'serious' | 'major' | 'catastrophic'

/** Correlation Engine incident record — mirrors GET /api/v1/incidents/{id} (IncidentRead). */
export interface Incident {
  id: string
  createdAt: string
  updatedAt: string
  primaryZoneId: string
  zoneName: string
  affectedZoneIds: string[]
  status: IncidentStatus
  origin: IncidentOrigin
  classification: IncidentClassification
  riskSeverityAtOpen: RiskLevel | null
  peakRiskSeverity: RiskLevel | null
  incidentSeverity: IncidentSeverity | null
  title: string
  summary: string
  openedAt: string
  resolvedAt: string | null
  closedAt: string | null
  rootCause: string | null
  correctiveActions: string[]
  openedById: string | null
  closedById: string | null
}
