import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { AlertTriangle, Plus, WifiOff } from 'lucide-react'
import { PageHeader } from '@/components/ui/PageHeader'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { StatusPill } from '@/components/ui/StatusPill'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/Table'
import { EmptyState } from '@/components/ui/EmptyState'
import { Skeleton } from '@/components/ui/Skeleton'
import { usePolling } from '@/hooks/usePolling'
import { buildIncidentPath, buildZonePath } from '@/app/routes'
import { riskLevelStatus } from '@/features/plant/utils/riskDisplay'
import { fetchIncidents } from '../services/incidentService'
import type { Incident, IncidentStatus } from '../types/incident'
import {
  INCIDENT_STATUS_LABEL,
  incidentClassificationBadgeVariant,
  incidentClassificationLabel,
  incidentOriginLabel,
  incidentStatusBadgeVariant,
} from '../utils/incidentDisplay'
import { formatRelativeTime } from '../utils/time'
import { IncidentActionCard } from '../components/IncidentActionCard'
import { ManualIncidentModal } from '../components/ManualIncidentModal'

const POLL_INTERVAL_MS = 5000

const FILTERS: Array<{ label: string; value: IncidentStatus | 'all' }> = [
  { label: 'Open', value: 'open' },
  { label: 'Resolved', value: 'resolved' },
  { label: 'Closed', value: 'closed' },
  { label: 'All', value: 'all' },
]

const RISK_RANK: Record<string, number> = { normal: 0, low: 1, moderate: 2, high: 3, critical: 4 }

/** The single most urgent still-open incident — same "answer what needs attention right now"
 * job the plant-wide Action Queue does for recommendations. */
function pickTopIncident(incidents: Incident[]): Incident | undefined {
  const open = incidents.filter((incident) => incident.status === 'open')
  if (open.length === 0) return undefined
  return [...open].sort((a, b) => {
    const rankA = RISK_RANK[a.peakRiskSeverity ?? 'normal'] ?? 0
    const rankB = RISK_RANK[b.peakRiskSeverity ?? 'normal'] ?? 0
    if (rankB !== rankA) return rankB - rankA
    return new Date(a.openedAt).getTime() - new Date(b.openedAt).getTime()
  })[0]
}

export function IncidentsListPage() {
  const navigate = useNavigate()
  const [filter, setFilter] = useState<IncidentStatus | 'all'>('open')
  const [isModalOpen, setIsModalOpen] = useState(false)

  const { data, error, isLoading } = usePolling(
    () => fetchIncidents({ status: filter === 'all' ? undefined : filter, pageSize: 100 }),
    POLL_INTERVAL_MS,
  )

  if (isLoading) {
    return (
      <div className="flex flex-col gap-6">
        <div className="flex flex-col gap-2 border-b border-border pb-5">
          <Skeleton className="h-7 w-48" />
          <Skeleton className="h-4 w-96" />
        </div>
        <Skeleton className="h-40" />
      </div>
    )
  }

  if (error || !data) {
    return (
      <EmptyState
        icon={WifiOff}
        title="Can't reach the incident log"
        description="The backend isn't responding. Make sure it's running, then this page will pick up automatically."
      />
    )
  }

  const topIncident = filter !== 'closed' ? pickTopIncident(data.items) : undefined

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Incidents"
        description="Bounded episodes the Correlation Engine has opened, plus anything an operator has logged by hand."
        actions={
          <Button size="sm" onClick={() => setIsModalOpen(true)}>
            <Plus className="h-3.5 w-3.5" aria-hidden="true" />
            Log Incident
          </Button>
        }
      />

      <div className="flex items-center gap-2">
        {FILTERS.map(({ label, value }) => (
          <Button
            key={value}
            size="sm"
            variant={filter === value ? 'secondary' : 'ghost'}
            onClick={() => setFilter(value)}
          >
            {label}
          </Button>
        ))}
      </div>

      {topIncident && <IncidentActionCard incident={topIncident} />}

      {data.items.length === 0 ? (
        <EmptyState
          icon={AlertTriangle}
          title="Nothing here"
          description="No incidents match this filter right now."
        />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Status</TableHead>
              <TableHead>Risk</TableHead>
              <TableHead>Incident</TableHead>
              <TableHead>Zone</TableHead>
              <TableHead>Classification</TableHead>
              <TableHead>Origin</TableHead>
              <TableHead>Opened</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.items.map((incident) => (
              <TableRow
                key={incident.id}
                className="cursor-pointer"
                onClick={() => navigate(buildIncidentPath(incident.id))}
              >
                <TableCell>
                  <Badge variant={incidentStatusBadgeVariant(incident.status)}>
                    {INCIDENT_STATUS_LABEL[incident.status]}
                  </Badge>
                </TableCell>
                <TableCell>
                  {incident.peakRiskSeverity ? (
                    <StatusPill
                      status={riskLevelStatus(incident.peakRiskSeverity)}
                      label={incident.peakRiskSeverity[0].toUpperCase() + incident.peakRiskSeverity.slice(1)}
                    />
                  ) : (
                    <span className="text-xs text-text-muted">—</span>
                  )}
                </TableCell>
                <TableCell>
                  <div className="flex max-w-xs flex-col">
                    <span className="font-medium text-text-primary">{incident.title}</span>
                    <span className="line-clamp-1 text-xs text-text-muted">{incident.summary}</span>
                  </div>
                </TableCell>
                <TableCell>
                  <Link
                    to={buildZonePath(incident.primaryZoneId)}
                    onClick={(event) => event.stopPropagation()}
                    className="text-text-secondary underline-offset-2 hover:text-text-primary hover:underline"
                  >
                    {incident.zoneName}
                  </Link>
                </TableCell>
                <TableCell>
                  <Badge variant={incidentClassificationBadgeVariant(incident.classification)}>
                    {incidentClassificationLabel(incident.classification)}
                  </Badge>
                </TableCell>
                <TableCell className="text-text-secondary">{incidentOriginLabel(incident.origin)}</TableCell>
                <TableCell className="text-text-secondary">{formatRelativeTime(incident.openedAt)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      <ManualIncidentModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} onCreated={() => {}} />
    </div>
  )
}
