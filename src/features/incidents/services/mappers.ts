import type { RiskLevel } from '@/features/plant/types/risk'
import type {
  Incident,
  IncidentClassification,
  IncidentOrigin,
  IncidentSeverity,
  IncidentStatus,
} from '../types/incident'
import type { RawIncident } from './wireTypes'

export function mapIncident(raw: RawIncident): Incident {
  return {
    id: raw.id,
    createdAt: raw.created_at,
    updatedAt: raw.updated_at,
    primaryZoneId: raw.primary_zone_id,
    zoneName: raw.zone_name,
    affectedZoneIds: raw.affected_zone_ids,
    status: raw.status as IncidentStatus,
    origin: raw.origin as IncidentOrigin,
    classification: raw.classification as IncidentClassification,
    riskSeverityAtOpen: raw.risk_severity_at_open as RiskLevel | null,
    peakRiskSeverity: raw.peak_risk_severity as RiskLevel | null,
    incidentSeverity: raw.incident_severity as IncidentSeverity | null,
    title: raw.title,
    summary: raw.summary,
    openedAt: raw.opened_at,
    resolvedAt: raw.resolved_at,
    closedAt: raw.closed_at,
    rootCause: raw.root_cause,
    correctiveActions: raw.corrective_actions,
    openedById: raw.opened_by_id,
    closedById: raw.closed_by_id,
  }
}
