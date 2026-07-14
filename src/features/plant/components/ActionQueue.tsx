import { ShieldCheck } from 'lucide-react'
import { Section } from '@/components/ui/Section'
import { useRecommendationActions } from '../hooks/useRecommendationActions'
import type { PlantRecommendationSummary } from '../types/recommendation'
import { RecommendationCard } from './RecommendationCard'

export interface ActionQueueProps {
  summary: PlantRecommendationSummary | null | undefined
}

/**
 * The plant-wide answer to "what should I do right now" — a short, priority-ranked queue
 * across every zone. The single most urgent item is presented as a command (ACTION REQUIRED);
 * everything else is a quieter supporting list, in descending priority. Each card's zone name
 * links through to that zone's own recommendations panel.
 */
export function ActionQueue({ summary }: ActionQueueProps) {
  const { visible, pendingIds, acknowledge, resolve } = useRecommendationActions(summary?.topRecommendations ?? [])

  if (summary == null) return null

  if (visible.length === 0) {
    return (
      <Section title="Action Queue" description="What operators should do right now, ranked across every zone.">
        <div className="flex items-center gap-3 rounded-lg border border-border bg-surface-sunken px-4 py-3.5">
          <ShieldCheck className="h-4 w-4 shrink-0 text-success" aria-hidden="true" />
          <p className="text-sm text-text-secondary">No active recommendations — every zone is within normal guidance.</p>
        </div>
      </Section>
    )
  }

  const [top, ...rest] = visible

  return (
    <Section title="Action Queue" description="What operators should do right now, ranked across every zone.">
      <div className="flex flex-col gap-3">
        <RecommendationCard
          recommendation={top}
          emphasized={top.priority === 'critical'}
          showZoneLabel
          isPending={pendingIds.has(top.id)}
          onAcknowledge={() => acknowledge(top.id)}
          onResolve={() => resolve(top.id)}
        />
        {rest.map((recommendation) => (
          <RecommendationCard
            key={recommendation.id}
            recommendation={recommendation}
            showZoneLabel
            isPending={pendingIds.has(recommendation.id)}
            onAcknowledge={() => acknowledge(recommendation.id)}
            onResolve={() => resolve(recommendation.id)}
          />
        ))}
      </div>
    </Section>
  )
}
