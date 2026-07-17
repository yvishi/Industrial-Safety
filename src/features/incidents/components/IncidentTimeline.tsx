import { Bot, User } from 'lucide-react'
import type { Status } from '@/types/common'
import type { PlantEvent } from '@/features/plant'
import { eventSeverityStatus } from '@/features/plant/utils/eventDisplay'
import { formatRelativeTime } from '../utils/time'

const DOT_CLASS: Record<Status, string> = {
  operational: 'bg-success',
  info: 'bg-info',
  warning: 'bg-warning',
  critical: 'bg-danger',
  offline: 'bg-text-muted',
}

export interface IncidentTimelineProps {
  events: PlantEvent[]
}

/** This incident's own bounded activity feed — the Operational Timeline's per-incident view,
 * read oldest-first so it tells the story in the order it happened. */
export function IncidentTimeline({ events }: IncidentTimelineProps) {
  if (events.length === 0) {
    return <p className="text-sm text-text-muted">No activity recorded for this incident yet.</p>
  }

  const chronological = [...events].sort(
    (a, b) => new Date(a.occurredAt).getTime() - new Date(b.occurredAt).getTime(),
  )

  return (
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
  )
}
