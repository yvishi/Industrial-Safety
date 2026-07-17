import { useEffect, useState } from 'react'
import { Link, Navigate, useLocation, useParams } from 'react-router-dom'
import { ArrowLeft, History, WifiOff } from 'lucide-react'
import { PageHeader } from '@/components/ui/PageHeader'
import { Badge } from '@/components/ui/Badge'
import { StatusPill } from '@/components/ui/StatusPill'
import { Section } from '@/components/ui/Section'
import { Skeleton } from '@/components/ui/Skeleton'
import { EmptyState } from '@/components/ui/EmptyState'
import { buttonVariants } from '@/components/ui/Button'
import { ROUTES, buildZonePath } from '@/app/routes'
import { usePolling } from '@/hooks/usePolling'
import { useBreadcrumbLabel } from '@/hooks/useBreadcrumbLabel'
import { ApiError } from '@/services/httpClient'
import { RISK_LEVEL_LABEL, riskLevelStatus } from '@/features/plant/utils/riskDisplay'
import { fetchIncident } from '../services/incidentService'
import type { Incident } from '../types/incident'
import {
  INCIDENT_STATUS_LABEL,
  incidentClassificationBadgeVariant,
  incidentClassificationLabel,
  incidentOriginLabel,
  incidentSeverityStatus,
  incidentStatusBadgeVariant,
} from '../utils/incidentDisplay'
import { IncidentNarrative } from '../components/IncidentNarrative'
import { IncidentRecommendations } from '../components/IncidentRecommendations'
import { IncidentActionsPanel } from '../components/IncidentActionsPanel'

const POLL_INTERVAL_MS = 5000

export function IncidentDetailPage() {
  const { incidentId } = useParams<{ incidentId: string }>()
  const location = useLocation()
  const [override, setOverride] = useState<Incident | null>(null)

  useEffect(() => {
    setOverride(null)
  }, [incidentId])

  const { data: polled, error, isLoading } = usePolling(
    () => (incidentId ? fetchIncident(incidentId) : Promise.reject(new Error('Missing incident id'))),
    POLL_INTERVAL_MS,
  )

  const incident = override ?? polled
  useBreadcrumbLabel(location.pathname, incident?.title)

  if (isLoading) {
    return (
      <div className="flex flex-col gap-6">
        <Skeleton className="h-4 w-32" />
        <div className="flex flex-col gap-2 border-b border-border pb-5">
          <Skeleton className="h-7 w-64" />
          <Skeleton className="h-4 w-96" />
        </div>
        <Skeleton className="h-24" />
      </div>
    )
  }

  if (error instanceof ApiError && error.status === 404) {
    return <Navigate to={ROUTES.incidents} replace />
  }

  if (error || !incident) {
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
      <Link
        to={ROUTES.incidents}
        className="inline-flex w-fit items-center gap-1.5 text-sm text-text-secondary transition-colors hover:text-text-primary"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden="true" />
        All incidents
      </Link>

      <PageHeader
        title={incident.title}
        actions={
          <div className="flex items-center gap-3">
            <Link
              to={buildZonePath(incident.primaryZoneId)}
              className="text-sm text-text-secondary underline-offset-2 hover:text-text-primary hover:underline"
            >
              {incident.zoneName}
            </Link>
            <Link
              to={`${ROUTES.timeline}?incidentId=${incident.id}`}
              className={buttonVariants({ variant: 'secondary', size: 'sm' })}
            >
              <History className="h-3.5 w-3.5" aria-hidden="true" />
              View Timeline
            </Link>
          </div>
        }
      />

      <div className="flex flex-wrap items-center gap-2">
        <Badge variant={incidentStatusBadgeVariant(incident.status)}>{INCIDENT_STATUS_LABEL[incident.status]}</Badge>
        {incident.peakRiskSeverity && (
          <StatusPill
            status={riskLevelStatus(incident.peakRiskSeverity)}
            label={`Risk: ${RISK_LEVEL_LABEL[incident.peakRiskSeverity]}`}
          />
        )}
        {incident.incidentSeverity && (
          <StatusPill
            status={incidentSeverityStatus(incident.incidentSeverity)}
            label={`Impact: ${incident.incidentSeverity[0].toUpperCase() + incident.incidentSeverity.slice(1)}`}
          />
        )}
        <Badge variant={incidentClassificationBadgeVariant(incident.classification)}>
          {incidentClassificationLabel(incident.classification)}
        </Badge>
        <Badge variant={incident.origin === 'manual' ? 'accent' : 'neutral'}>
          {incidentOriginLabel(incident.origin)}
        </Badge>
      </div>

      <IncidentNarrative incident={incident} />

      <div className="grid gap-4 sm:grid-cols-3">
        <MetaField label="Opened" value={new Date(incident.openedAt).toLocaleString()} />
        <MetaField label="Resolved" value={incident.resolvedAt ? new Date(incident.resolvedAt).toLocaleString() : '—'} />
        <MetaField label="Closed" value={incident.closedAt ? new Date(incident.closedAt).toLocaleString() : '—'} />
      </div>

      {incident.rootCause && (
        <Section title="Root Cause">
          <p className="text-sm text-text-secondary">{incident.rootCause}</p>
        </Section>
      )}

      {incident.correctiveActions.length > 0 && (
        <Section title="Corrective Actions">
          <ul className="flex flex-col gap-1.5">
            {incident.correctiveActions.map((action) => (
              <li key={action} className="text-sm text-text-secondary">
                • {action}
              </li>
            ))}
          </ul>
        </Section>
      )}

      <Section title="Linked Recommendations" description="What the Recommendation Engine advised while this was open.">
        <IncidentRecommendations
          zoneId={incident.primaryZoneId}
          incidentId={incident.id}
          includeResolved={incident.status !== 'open'}
        />
      </Section>

      {incident.status !== 'closed' && (
        <Section title="Actions" description="Log a note, reclassify, or close this incident out.">
          <IncidentActionsPanel incident={incident} onChange={setOverride} />
        </Section>
      )}
    </div>
  )
}

function MetaField({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-0.5 rounded-lg border border-border p-3">
      <span className="text-xs font-medium uppercase tracking-wide text-text-muted">{label}</span>
      <span className="text-sm text-text-primary">{value}</span>
    </div>
  )
}
