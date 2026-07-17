import { Link } from 'react-router-dom'
import { ArrowRight, Clock } from 'lucide-react'
import { ROUTES, buildIncidentPath } from '@/app/routes'
import { Section } from '@/components/ui/Section'
import { EmptyState } from '@/components/ui/EmptyState'
import { Badge } from '@/components/ui/Badge'
import { EVENT_SEVERITY_LABEL, eventSeverityStatus } from '@/features/plant/utils/eventDisplay'
import { formatRelativeTime } from '@/features/plant/utils/time'
import type { PlantEvent } from '@/features/plant/types/event'
import type { Status } from '@/types/common'

export interface RecentActivityFeedProps {
  /** Already sorted newest-first and already sliced to the number of rows to display (e.g. top
   * 8) — do not re-sort or re-slice here. */
  events: PlantEvent[]
}

/** Status -> left border color. Kept exhaustive over the shared 5-slot Status union even though
 * event severity never actually produces 'offline'. */
const STATUS_BORDER_CLASS: Record<Status, string> = {
  operational: 'border-success',
  info: 'border-info',
  warning: 'border-warning',
  critical: 'border-danger',
  offline: 'border-border',
}

/**
 * Answers "what changed recently" — a quiet, chronological feed of plant events. Deliberately
 * restrained: the top safety banner elsewhere on the dashboard is the one loud element.
 */
export function RecentActivityFeed({ events }: RecentActivityFeedProps) {
  return (
    <Section
      title="Recent Activity"
      description="What changed across the plant, most recent first."
      actions={
        <Link to={ROUTES.timeline} className="flex items-center gap-1 text-sm text-accent hover:underline">
          View timeline
          <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
        </Link>
      }
    >
      {events.length === 0 ? (
        <EmptyState icon={Clock} title="No recent activity" description="Nothing has changed yet." />
      ) : (
        <div className="flex flex-col gap-3">
          {events.map((event) => (
            <div
              key={event.id}
              className={`border-l-2 pl-3 ${STATUS_BORDER_CLASS[eventSeverityStatus(event.severity)]}`}
            >
              <div className="flex flex-col gap-0.5">
                <span className="text-sm text-text-primary">{event.title}</span>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-text-muted">{formatRelativeTime(event.occurredAt)}</span>
                  {(event.severity === 'warning' || event.severity === 'critical') && (
                    <Badge variant={event.severity === 'critical' ? 'danger' : 'warning'}>
                      {EVENT_SEVERITY_LABEL[event.severity]}
                    </Badge>
                  )}
                </div>
                {event.description != null && (
                  <p className="text-xs text-text-secondary line-clamp-1">{event.description}</p>
                )}
                {event.incidentId != null && (
                  <Link
                    to={buildIncidentPath(event.incidentId)}
                    className="text-xs text-accent hover:underline"
                  >
                    View incident →
                  </Link>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </Section>
  )
}
