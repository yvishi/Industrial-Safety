import { useState } from 'react'
import { ShieldCheck } from 'lucide-react'
import { usePolling } from '@/hooks/usePolling'
import { RecommendationCard } from '@/features/plant/components/RecommendationCard'
import { fetchZoneRecommendations, acknowledgeRecommendation, resolveRecommendation } from '@/features/plant/services/recommendationService'

const POLL_INTERVAL_MS = 5000

export interface IncidentRecommendationsProps {
  zoneId: string
  incidentId: string
  /** Closed/resolved incidents may reference a recommendation that has itself since resolved —
   * only fetch that history for incidents that are no longer open. */
  includeResolved: boolean
}

/** The recommendations the Correlation Engine actually linked to this incident — reuses
 * RecommendationCard as-is so a recommendation looks identical whether seen from a zone page
 * or from here. */
export function IncidentRecommendations({ zoneId, incidentId, includeResolved }: IncidentRecommendationsProps) {
  const [pendingIds, setPendingIds] = useState<Set<string>>(new Set())
  const { data } = usePolling(
    () => fetchZoneRecommendations(zoneId, includeResolved),
    POLL_INTERVAL_MS,
  )

  const linked = (data ?? []).filter((recommendation) => recommendation.incidentId === incidentId)

  if (linked.length === 0) {
    return (
      <div className="flex items-center gap-3 rounded-lg border border-border bg-surface-sunken px-4 py-3.5">
        <ShieldCheck className="h-4 w-4 shrink-0 text-success" aria-hidden="true" />
        <p className="text-sm text-text-secondary">No recommendations are linked to this incident.</p>
      </div>
    )
  }

  async function withPending(id: string, run: () => Promise<void>) {
    setPendingIds((prev) => new Set(prev).add(id))
    try {
      await run()
    } finally {
      setPendingIds((prev) => {
        const next = new Set(prev)
        next.delete(id)
        return next
      })
    }
  }

  return (
    <div className="flex flex-col gap-3">
      {linked.map((recommendation) => (
        <RecommendationCard
          key={recommendation.id}
          recommendation={recommendation}
          isPending={pendingIds.has(recommendation.id)}
          onAcknowledge={() => withPending(recommendation.id, async () => void (await acknowledgeRecommendation(recommendation.id)))}
          onResolve={() => withPending(recommendation.id, async () => void (await resolveRecommendation(recommendation.id)))}
        />
      ))}
    </div>
  )
}
