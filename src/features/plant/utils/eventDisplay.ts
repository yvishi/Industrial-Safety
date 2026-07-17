import type { Status } from '@/types/common'
import type { EventSeverity } from '../types/event'

export const EVENT_SEVERITY_LABEL: Record<EventSeverity, string> = {
  info: 'Info',
  notice: 'Notice',
  warning: 'Warning',
  critical: 'Critical',
}

/** Reuses the same 5-slot Status scale as riskLevelStatus/recommendationPriorityStatus —
 * event severity is its own scale but should read as the same color language. */
export function eventSeverityStatus(severity: EventSeverity): Status {
  switch (severity) {
    case 'info':
      return 'operational'
    case 'notice':
      return 'info'
    case 'warning':
      return 'warning'
    case 'critical':
      return 'critical'
  }
}
