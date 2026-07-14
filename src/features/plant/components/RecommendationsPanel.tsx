import { ShieldCheck } from 'lucide-react'
import { Skeleton } from '@/components/ui/Skeleton'
import { usePolling } from '@/hooks/usePolling'
import { useRecommendationActions } from '../hooks/useRecommendationActions'
import { fetchZoneRecommendations } from '../services/recommendationService'
import { RecommendationCard } from './RecommendationCard'

const POLL_INTERVAL_MS = 5000

export interface RecommendationsPanelProps {
  zoneId: string
}

/** Zone-level Recommended Actions panel — the full-detail counterpart to the plant-wide
 * Action Queue, scoped to this zone. */
export function RecommendationsPanel({ zoneId }: RecommendationsPanelProps) {
  const { data: recommendations, isLoading } = usePolling(
    () => fetchZoneRecommendations(zoneId),
    POLL_INTERVAL_MS,
  )
  const { visible, pendingIds, acknowledge, resolve } = useRecommendationActions(recommendations ?? [])

  if (isLoading) {
    return (
      <div className="flex flex-col gap-3">
        <Skeleton className="h-24" />
        <Skeleton className="h-16" />
      </div>
    )
  }

  if (visible.length === 0) {
    return (
      <div className="flex items-center gap-3 rounded-lg border border-border bg-surface-sunken px-4 py-3.5">
        <ShieldCheck className="h-4 w-4 shrink-0 text-success" aria-hidden="true" />
        <p className="text-sm text-text-secondary">No active recommendations for this zone.</p>
      </div>
    )
  }

  const [top, ...rest] = visible

  return (
    <div className="flex flex-col gap-3">
      <RecommendationCard
        recommendation={top}
        emphasized={top.priority === 'critical'}
        isPending={pendingIds.has(top.id)}
        onAcknowledge={() => acknowledge(top.id)}
        onResolve={() => resolve(top.id)}
      />
      {rest.map((recommendation) => (
        <RecommendationCard
          key={recommendation.id}
          recommendation={recommendation}
          isPending={pendingIds.has(recommendation.id)}
          onAcknowledge={() => acknowledge(recommendation.id)}
          onResolve={() => resolve(recommendation.id)}
        />
      ))}
    </div>
  )
}
