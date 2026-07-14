import type { Status } from '@/types/common'
import type { RecommendationPriority, RecommendationState } from '../types/recommendation'

export const RECOMMENDATION_PRIORITY_LABEL: Record<RecommendationPriority, string> = {
  critical: 'Critical',
  high: 'High',
  moderate: 'Moderate',
  low: 'Low',
}

/** Reuses the same 5-slot Status scale as riskLevelStatus — recommendation priority and risk
 * level are different measurements but should read as the same color language. */
export function recommendationPriorityStatus(priority: RecommendationPriority): Status {
  switch (priority) {
    case 'critical':
      return 'critical'
    case 'high':
    case 'moderate':
      return 'warning'
    case 'low':
      return 'info'
  }
}

export const RECOMMENDATION_STATE_LABEL: Record<RecommendationState, string> = {
  new: 'New',
  acknowledged: 'Acknowledged',
  resolved: 'Resolved',
}
