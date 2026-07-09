import type { Status } from '@/types/common'
import type { EquipmentStatus } from '../types/equipment'
import type { PermitStatus } from '../types/permit'
import type { SensorStatus } from '../types/sensor'

/**
 * Maps each domain's literal status field to StatusPill's neutral vocabulary. This reflects
 * the field's own recorded value only — no risk scoring or judgment is computed here.
 */

export function equipmentStatusPill(status: EquipmentStatus): Status {
  switch (status) {
    case 'operational':
      return 'operational'
    case 'standby':
      return 'info'
    case 'under_maintenance':
      return 'warning'
    case 'decommissioned':
      return 'offline'
  }
}

export function sensorStatusPill(status: SensorStatus): Status {
  switch (status) {
    case 'active':
      return 'operational'
    case 'under_calibration':
      return 'warning'
    case 'faulted':
      return 'critical'
    case 'inactive':
      return 'offline'
  }
}

export function permitStatusPill(status: PermitStatus): Status {
  switch (status) {
    case 'active':
      return 'operational'
    case 'approved':
      return 'info'
    case 'pending_approval':
      return 'warning'
    case 'revoked':
      return 'critical'
    case 'draft':
    case 'closed':
    case 'expired':
      return 'offline'
  }
}

const STATUS_LABEL_OVERRIDES: Record<string, string> = {
  under_maintenance: 'Under Maintenance',
  under_calibration: 'Under Calibration',
  pending_approval: 'Pending Approval',
}

/** "under_maintenance" -> "Under Maintenance"; falls back to a title-cased split on "_". */
export function formatStatusLabel(status: string): string {
  if (status in STATUS_LABEL_OVERRIDES) return STATUS_LABEL_OVERRIDES[status]
  return status
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}
