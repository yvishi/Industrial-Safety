import { useState } from 'react'
import { acknowledgeRecommendation, resolveRecommendation } from '../services/recommendationService'
import type { Recommendation, RecommendationState } from '../types/recommendation'

/**
 * Wraps a polled recommendation list with optimistic acknowledge/resolve — usePolling has no
 * manual refetch, so without this the UI would sit still for up to one 5s poll interval after
 * an operator acts. The next real poll always wins; these overrides just bridge the gap.
 */
export function useRecommendationActions(recommendations: Recommendation[]) {
  const [stateOverrides, setStateOverrides] = useState<Record<string, RecommendationState>>({})
  const [resolvedIds, setResolvedIds] = useState<Set<string>>(new Set())
  const [pendingIds, setPendingIds] = useState<Set<string>>(new Set())

  const visible = recommendations
    .filter((r) => !resolvedIds.has(r.id))
    .map((r) => (stateOverrides[r.id] ? { ...r, state: stateOverrides[r.id] } : r))

  function withPending(id: string, run: () => Promise<void>) {
    setPendingIds((prev) => new Set(prev).add(id))
    run().finally(() => {
      setPendingIds((prev) => {
        const next = new Set(prev)
        next.delete(id)
        return next
      })
    })
  }

  function acknowledge(id: string) {
    withPending(id, async () => {
      await acknowledgeRecommendation(id)
      setStateOverrides((prev) => ({ ...prev, [id]: 'acknowledged' }))
    })
  }

  function resolve(id: string) {
    withPending(id, async () => {
      await resolveRecommendation(id)
      setResolvedIds((prev) => new Set(prev).add(id))
    })
  }

  return { visible, pendingIds, acknowledge, resolve }
}
