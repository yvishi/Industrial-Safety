import { WifiOff } from 'lucide-react'
import { PageHeader } from '@/components/ui/PageHeader'
import { Badge } from '@/components/ui/Badge'
import { Skeleton } from '@/components/ui/Skeleton'
import { EmptyState } from '@/components/ui/EmptyState'
import { usePolling } from '@/hooks/usePolling'
import { ZoneGrid } from '../components/ZoneGrid'
import { LiveIndicator } from '../components/LiveIndicator'
import { fetchPlantState } from '../services/plantService'

const POLL_INTERVAL_MS = 5000

function ZoneGridSkeleton() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {Array.from({ length: 8 }).map((_, index) => (
        <Skeleton key={index} className="h-36" />
      ))}
    </div>
  )
}

export function PlantOverviewPage() {
  const { data: state, error, isLoading } = usePolling(fetchPlantState, POLL_INTERVAL_MS)

  if (isLoading) {
    return (
      <div className="flex flex-col gap-6">
        <div className="flex flex-col gap-2 border-b border-border pb-5">
          <Skeleton className="h-7 w-64" />
          <Skeleton className="h-4 w-48" />
        </div>
        <ZoneGridSkeleton />
      </div>
    )
  }

  if (error || !state) {
    return (
      <EmptyState
        icon={WifiOff}
        title="Can't reach the plant"
        description={`The backend API isn't responding. Make sure it's running, then this page will pick up automatically.`}
      />
    )
  }

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
      <ZoneGrid zones={state.zones} />
    </div>
  )
}
