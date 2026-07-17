import { useState } from 'react'
import { Bot, User } from 'lucide-react'
import type { Status } from '@/types/common'
import { Button } from '@/components/ui/Button'
import { Skeleton } from '@/components/ui/Skeleton'
import { usePolling } from '@/hooks/usePolling'
import { fetchEvents } from '@/features/plant/services/plantService'
import { eventSeverityStatus } from '@/features/plant/utils/eventDisplay'
import { formatRelativeTime } from '../utils/time'

const POLL_INTERVAL_MS = 5000
const PAGE_SIZE = 20

const DOT_CLASS: Record<Status, string> = {
  operational: 'bg-success',
  info: 'bg-info',
  warning: 'bg-warning',
  critical: 'bg-danger',
  offline: 'bg-text-muted',
}

export interface IncidentTimelineProps {
  incidentId: string
}

/** This incident's own bounded activity feed — the Operational Timeline's per-incident view,
 * read oldest-first so it tells the story in the order it happened. Loads a small, recent
 * window first rather than the whole history at once; "Load earlier activity" pulls in more
 * on demand instead of every view paying for events nobody's asked to see yet. */
export function IncidentTimeline({ incidentId }: IncidentTimelineProps) {
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE)

  // Remounting on visibleCount change (via key) is what makes "Load earlier" feel instant:
  // usePolling only picks up a changed fetcher on its *next* scheduled tick (up to 5s later),
  // since its effect intentionally doesn't restart on every render — see its own docstring.
  // A fresh mount runs that effect immediately instead of waiting out the interval.
  return <TimelineWindow key={visibleCount} incidentId={incidentId} visibleCount={visibleCount} onLoadMore={() => setVisibleCount((count) => count + PAGE_SIZE)} />
}

function TimelineWindow({
  incidentId,
  visibleCount,
  onLoadMore,
}: {
  incidentId: string
  visibleCount: number
  onLoadMore: () => void
}) {
  const { data, isLoading } = usePolling(
    () => fetchEvents({ incidentId, pageSize: visibleCount }),
    POLL_INTERVAL_MS,
  )

  if (isLoading) {
    return (
      <div className="flex flex-col gap-2">
        {Array.from({ length: 4 }).map((_, index) => (
          <Skeleton key={index} className="h-12" />
        ))}
      </div>
    )
  }

  const events = data?.items ?? []
  const total = data?.total ?? 0
  const remaining = total - events.length

  if (events.length === 0) {
    return <p className="text-sm text-text-muted">No activity recorded for this incident yet.</p>
  }

  const chronological = [...events].sort(
    (a, b) => new Date(a.occurredAt).getTime() - new Date(b.occurredAt).getTime(),
  )

  return (
    <div className="flex flex-col gap-3">
      {remaining > 0 && (
        <Button variant="outline" size="sm" onClick={onLoadMore} className="self-center">
          Load earlier activity ({remaining} more)
        </Button>
      )}
      <ul className="flex flex-col divide-y divide-border rounded-lg border border-border">
        {chronological.map((event) => {
          const ActorIcon = event.actorType === 'operator' ? User : Bot
          return (
            <li key={event.id} className="flex items-start gap-3 px-4 py-3">
              <span
                className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${DOT_CLASS[eventSeverityStatus(event.severity)]}`}
                aria-hidden="true"
              />
              <div className="flex min-w-0 flex-1 flex-col gap-0.5">
                <span className="text-sm text-text-primary">{event.title}</span>
                {event.description && <p className="text-sm text-text-secondary">{event.description}</p>}
              </div>
              <span className="flex shrink-0 items-center gap-1.5 text-xs text-text-muted" title={event.actorType}>
                <ActorIcon className="h-3.5 w-3.5" aria-hidden="true" />
                {formatRelativeTime(event.occurredAt)}
              </span>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
