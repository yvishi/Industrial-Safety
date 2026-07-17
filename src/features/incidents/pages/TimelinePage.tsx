import { useMemo } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { History, WifiOff } from 'lucide-react'
import { PageHeader } from '@/components/ui/PageHeader'
import { Badge } from '@/components/ui/Badge'
import { EmptyState } from '@/components/ui/EmptyState'
import { Skeleton } from '@/components/ui/Skeleton'
import { usePolling } from '@/hooks/usePolling'
import { buildIncidentPath } from '@/app/routes'
import { cn } from '@/utils/cn'
import { fetchIncidents } from '../services/incidentService'
import type { Incident } from '../types/incident'
import { INCIDENT_STATUS_LABEL, incidentStatusBadgeVariant } from '../utils/incidentDisplay'
import { formatRelativeTime } from '../utils/time'
import { IncidentTimeline } from '../components/IncidentTimeline'

const POLL_INTERVAL_MS = 5000

/**
 * The Operational Timeline: every incident's own chronological record, in one place — pick
 * one from the list on the left (newest-first) to see its timeline on the right. Arriving
 * here from an incident's own "View Timeline" link (?incidentId=...) opens straight to that
 * incident's timeline instead of making the operator find it again.
 */
export function TimelinePage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const requestedIncidentId = searchParams.get('incidentId')

  const { data: incidentPage, error, isLoading } = usePolling(
    () => fetchIncidents({ pageSize: 100 }),
    POLL_INTERVAL_MS,
  )

  const incidents = useMemo(
    () =>
      [...(incidentPage?.items ?? [])].sort(
        (a, b) => new Date(b.openedAt).getTime() - new Date(a.openedAt).getTime(),
      ),
    [incidentPage],
  )

  // Deep-linked incident wins; otherwise default to the most recently opened one so the page
  // never opens empty when there's something to show.
  const activeIncident: Incident | undefined =
    incidents.find((incident) => incident.id === requestedIncidentId) ?? incidents[0]

  function selectIncident(incident: Incident) {
    setSearchParams({ incidentId: incident.id })
  }

  if (isLoading) {
    return (
      <div className="flex flex-col gap-6">
        <div className="flex flex-col gap-2 border-b border-border pb-5">
          <Skeleton className="h-7 w-48" />
          <Skeleton className="h-4 w-72" />
        </div>
        <Skeleton className="h-64" />
      </div>
    )
  }

  if (error || !incidentPage) {
    return (
      <EmptyState
        icon={WifiOff}
        title="Can't reach the incident log"
        description="The backend isn't responding. Make sure it's running, then this page will pick up automatically."
      />
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Timeline" description="Every incident's own chronological record, in one place." />

      {incidents.length === 0 ? (
        <EmptyState
          icon={History}
          title="No incidents yet"
          description="Once an incident opens, its timeline will appear here."
        />
      ) : (
        <div className="grid gap-6 lg:grid-cols-[18rem_minmax(0,1fr)]">
          <nav className="flex flex-col gap-1 lg:border-r lg:border-border lg:pr-4">
            {incidents.map((incident) => (
              <button
                key={incident.id}
                type="button"
                onClick={() => selectIncident(incident)}
                className={cn(
                  'flex flex-col items-start gap-1 rounded-md px-3 py-2 text-left transition-colors',
                  incident.id === activeIncident?.id ? 'bg-accent-subtle' : 'hover:bg-surface-hover',
                )}
              >
                <span className="flex w-full items-center gap-2">
                  <Badge variant={incidentStatusBadgeVariant(incident.status)}>
                    {INCIDENT_STATUS_LABEL[incident.status]}
                  </Badge>
                  <span className="ml-auto text-xs text-text-muted">{formatRelativeTime(incident.openedAt)}</span>
                </span>
                <span className="line-clamp-1 text-sm font-medium text-text-primary">{incident.title}</span>
                <span className="text-xs text-text-muted">{incident.zoneName}</span>
              </button>
            ))}
          </nav>

          {activeIncident && (
            <div className="flex flex-col gap-4">
              <div className="flex items-center justify-between gap-3 border-b border-border pb-3">
                <div className="flex flex-col gap-0.5">
                  <span className="text-sm font-semibold text-text-primary">{activeIncident.title}</span>
                  <span className="text-xs text-text-muted">{activeIncident.zoneName}</span>
                </div>
                <Link
                  to={buildIncidentPath(activeIncident.id)}
                  className="shrink-0 text-xs text-text-secondary underline-offset-2 hover:text-text-primary hover:underline"
                >
                  Open incident
                </Link>
              </div>
              <IncidentTimeline incidentId={activeIncident.id} />
            </div>
          )}
        </div>
      )}
    </div>
  )
}
