import type { PlantEvent } from '../types/event'
import { formatStatusLabel } from '../utils/statusMapping'
import { formatRelativeTime } from '../utils/time'

export interface ActivityListProps {
  events: PlantEvent[]
}

export function ActivityList({ events }: ActivityListProps) {
  if (events.length === 0) {
    return <p className="text-sm text-text-muted">No recent activity in this zone.</p>
  }

  return (
    <ul className="flex flex-col divide-y divide-border rounded-lg border border-border">
      {events.map((event) => (
        <li key={event.id} className="flex items-start justify-between gap-3 px-4 py-3">
          <div className="flex min-w-0 flex-1 flex-col">
            <span className="truncate text-sm text-text-primary">{event.title}</span>
            <span className="text-xs text-text-muted">{formatStatusLabel(event.eventType)}</span>
          </div>
          <span className="shrink-0 text-xs text-text-muted">
            {formatRelativeTime(event.occurredAt)}
          </span>
        </li>
      ))}
    </ul>
  )
}
