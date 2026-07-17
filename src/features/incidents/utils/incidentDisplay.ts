import type { Status } from '@/types/common'
import type {
  IncidentClassification,
  IncidentOrigin,
  IncidentSeverity,
  IncidentStatus,
} from '../types/incident'

/** Workflow status -> Badge variant (for a plain Badge, not StatusPill — this is lifecycle,
 * not severity). */
export function incidentStatusBadgeVariant(status: IncidentStatus): 'warning' | 'info' | 'success' {
  switch (status) {
    case 'open':
      return 'warning'
    case 'resolved':
      return 'info'
    case 'closed':
      return 'success'
  }
}

export const INCIDENT_STATUS_LABEL: Record<IncidentStatus, string> = {
  open: 'Open',
  resolved: 'Resolved',
  closed: 'Closed',
}

export function incidentOriginLabel(origin: IncidentOrigin): string {
  switch (origin) {
    case 'system_detected':
      return 'Auto-detected'
    case 'manual':
      return 'Manually reported'
  }
}

/** Classification -> Badge variant — flags reportable_incident visually since it's
 * compliance-relevant. */
export function incidentClassificationBadgeVariant(
  classification: IncidentClassification,
): 'neutral' | 'danger' {
  return classification === 'reportable_incident' ? 'danger' : 'neutral'
}

export function incidentClassificationLabel(classification: IncidentClassification): string {
  switch (classification) {
    case 'operational_episode':
      return 'Operational Episode'
    case 'near_miss':
      return 'Near Miss'
    case 'safety_incident':
      return 'Safety Incident'
    case 'reportable_incident':
      return 'Reportable Incident'
  }
}

/** 5-tier incident_severity -> the shared Status union — reuses the same 5-slot scale as
 * riskLevelStatus (see plant/utils/riskDisplay.ts) so severity colors read consistently
 * across features. */
export function incidentSeverityStatus(severity: IncidentSeverity): Status {
  switch (severity) {
    case 'negligible':
      return 'operational'
    case 'minor':
      return 'info'
    case 'serious':
    case 'major':
      return 'warning'
    case 'catastrophic':
      return 'critical'
  }
}
