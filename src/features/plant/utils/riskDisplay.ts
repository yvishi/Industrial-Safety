import type { Status } from '@/types/common'
import type { RiskLevel } from '../types/risk'

export const RISK_LEVEL_LABEL: Record<RiskLevel, string> = {
  normal: 'Normal',
  low: 'Low',
  moderate: 'Moderate',
  high: 'High',
  critical: 'Critical',
}

/** StatusPill only has 5 slots; moderate/high share "warning" since risk severity is a
 * distinct scale from equipment/sensor operational status — critical is what must stand out. */
export function riskLevelStatus(level: RiskLevel): Status {
  switch (level) {
    case 'normal':
      return 'operational'
    case 'low':
      return 'info'
    case 'moderate':
    case 'high':
      return 'warning'
    case 'critical':
      return 'critical'
  }
}

export const RISK_LEVEL_BORDER_CLASS: Record<RiskLevel, string> = {
  normal: 'border-t-success',
  low: 'border-t-info',
  moderate: 'border-t-warning',
  high: 'border-t-warning',
  critical: 'border-t-danger',
}
