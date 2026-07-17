import { WifiOff } from 'lucide-react'
import { PageHeader } from '@/components/ui/PageHeader'
import { Badge } from '@/components/ui/Badge'
import { Skeleton } from '@/components/ui/Skeleton'
import { EmptyState } from '@/components/ui/EmptyState'
import { usePolling } from '@/hooks/usePolling'
import { LiveIndicator } from '@/features/plant/components/LiveIndicator'
import { fetchPlantState } from '@/features/plant/services/plantService'
import { fetchPlantRisk } from '@/features/plant/services/riskService'
import { fetchIncidents } from '@/features/incidents/services/incidentService'
import { SafetyStatusBand } from '@/features/dashboard/components/SafetyStatusBand'
import { DashboardKpiRow } from '@/features/dashboard/components/DashboardKpiRow'
import { IncidentsAttentionList } from '@/features/dashboard/components/IncidentsAttentionList'
import { RecentActivityFeed } from '@/features/dashboard/components/RecentActivityFeed'
import { computeSafetyVerdict, isUrgentIncident, sortByUrgency } from '@/features/dashboard/utils/safetyVerdict'

const POLL_INTERVAL_MS = 5000
const MAX_ATTENTION_ROWS = 5
const MAX_ACTIVITY_ROWS = 8

function DashboardSkeleton() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-2 border-b border-border pb-5">
        <Skeleton className="h-7 w-64" />
        <Skeleton className="h-4 w-48" />
      </div>
      <Skeleton className="h-32" />
      <div className="grid gap-4 sm:grid-cols-3">
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
      </div>
      <Skeleton className="h-64" />
      <Skeleton className="h-64" />
    </div>
  )
}

/**
 * The plant-wide answer to "is the refinery safe" in one glance: a headline safety verdict,
 * then the three numbers that matter (open incidents, most critical zone, urgent incidents),
 * then what needs action now, then what changed recently. Composes the Correlation Engine
 * (incidents), Compound Risk Engine (per-zone risk), and plant state — no new backend surface.
 */
export function DashboardPage() {
  const { data: state, error: stateError, isLoading: stateLoading } = usePolling(fetchPlantState, POLL_INTERVAL_MS)
  const { data: riskSummary, error: riskError, isLoading: riskLoading } = usePolling(fetchPlantRisk, POLL_INTERVAL_MS)
  const {
    data: incidentPage,
    error: incidentsError,
    isLoading: incidentsLoading,
  } = usePolling(() => fetchIncidents({ status: 'open', pageSize: 100 }), POLL_INTERVAL_MS)

  if (stateLoading || riskLoading || incidentsLoading) {
    return <DashboardSkeleton />
  }

  if (stateError || riskError || incidentsError || !state || !riskSummary || !incidentPage) {
    return (
      <EmptyState
        icon={WifiOff}
        title="Can't reach the refinery"
        description="The refinery data service isn't responding. Make sure the backend is running, then this page will pick up automatically."
      />
    )
  }

  const openIncidents = incidentPage.items
  const verdict = computeSafetyVerdict(riskSummary, openIncidents)
  const urgentIncidentCount = openIncidents.filter(isUrgentIncident).length
  const attentionIncidents = sortByUrgency(openIncidents).slice(0, MAX_ATTENTION_ROWS)

  const highestRiskZone = riskSummary.zones.find((zone) => zone.zoneId === riskSummary.highestRiskZoneId)
  const mostCriticalZone = highestRiskZone
    ? {
        zoneId: highestRiskZone.zoneId,
        zoneName: highestRiskZone.zoneName,
        level: highestRiskZone.level,
        score: highestRiskZone.score,
      }
    : null

  const recentEvents = [...state.recentEvents]
    .sort((a, b) => new Date(b.occurredAt).getTime() - new Date(a.occurredAt).getTime())
    .slice(0, MAX_ACTIVITY_ROWS)

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title={state.plant.name}
        description={`${state.plant.location} — ${state.zones.length} zones`}
        actions={
          <div className="flex items-center gap-3">
            <LiveIndicator generatedAt={state.generatedAt} />
            <Badge variant="neutral" className="font-mono">
              {state.plant.code}
            </Badge>
          </div>
        }
      />

      <SafetyStatusBand verdict={verdict} />

      <DashboardKpiRow
        openIncidentCount={incidentPage.total}
        urgentIncidentCount={urgentIncidentCount}
        mostCriticalZone={mostCriticalZone}
      />

      <IncidentsAttentionList incidents={attentionIncidents} totalOpenCount={incidentPage.total} />

      <RecentActivityFeed events={recentEvents} />
    </div>
  )
}
