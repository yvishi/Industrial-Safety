import { useParams, useLocation, Link, Navigate } from 'react-router-dom'
import { ArrowLeft, ScanEye, Sparkles, WifiOff } from 'lucide-react'
import { PageHeader } from '@/components/ui/PageHeader'
import { Badge } from '@/components/ui/Badge'
import { Section } from '@/components/ui/Section'
import { Skeleton } from '@/components/ui/Skeleton'
import { EmptyState } from '@/components/ui/EmptyState'
import { ROUTES } from '@/app/routes'
import { usePolling } from '@/hooks/usePolling'
import { useBreadcrumbLabel } from '@/hooks/useBreadcrumbLabel'
import { ZoneTypeIcon, ZONE_TYPE_LABEL } from '../components/ZoneTypeIcon'
import { CapabilityPlaceholder } from '../components/CapabilityPlaceholder'
import { LiveIndicator } from '../components/LiveIndicator'
import { PersonnelList } from '../components/PersonnelList'
import { EquipmentList } from '../components/EquipmentList'
import { SensorList } from '../components/SensorList'
import { PermitList } from '../components/PermitList'
import { ActivityList } from '../components/ActivityList'
import { fetchPlantState, fetchZoneEvents } from '../services/plantService'

const POLL_INTERVAL_MS = 5000

const UPCOMING_CAPABILITIES = [
  {
    icon: ScanEye,
    title: 'Computer Vision',
    description: 'Camera-based hazard and PPE detection for this process area. Not yet connected.',
  },
  {
    icon: Sparkles,
    title: 'AI Recommendations',
    description: 'Model-generated safety guidance for this process area. Not yet connected.',
  },
]

export function ZoneDetailPage() {
  const { zoneId } = useParams<{ zoneId: string }>()
  const location = useLocation()
  const { data: state, error, isLoading } = usePolling(fetchPlantState, POLL_INTERVAL_MS)
  const { data: events } = usePolling(
    () => (zoneId ? fetchZoneEvents(zoneId) : Promise.resolve([])),
    POLL_INTERVAL_MS,
  )

  const zoneState = state?.zones.find((entry) => entry.zone.id === zoneId)
  useBreadcrumbLabel(location.pathname, zoneState?.zone.name)

  if (isLoading) {
    return (
      <div className="flex flex-col gap-6">
        <Skeleton className="h-4 w-32" />
        <div className="flex flex-col gap-2 border-b border-border pb-5">
          <Skeleton className="h-7 w-64" />
          <Skeleton className="h-4 w-96" />
        </div>
        <Skeleton className="h-48" />
      </div>
    )
  }

  if (error || !state) {
    return (
      <EmptyState
        icon={WifiOff}
        title="Can't reach the refinery"
        description="The refinery data service isn't responding. Make sure the backend is running, then this page will pick up automatically."
      />
    )
  }

  if (!zoneState) {
    return <Navigate to={ROUTES.plant} replace />
  }

  const { zone, workers, equipment, sensors } = zoneState
  const activePermits = state.activePermits.filter((permit) => permit.zoneId === zone.id)

  return (
    <div className="flex flex-col gap-6">
      <Link
        to={ROUTES.plant}
        className="inline-flex w-fit items-center gap-1.5 text-sm text-text-secondary transition-colors hover:text-text-primary"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden="true" />
        Refinery overview
      </Link>

      <PageHeader
        title={zone.name}
        description={zone.description ?? undefined}
        actions={
          <div className="flex items-center gap-3">
            <LiveIndicator generatedAt={state.generatedAt} />
            <Badge variant="neutral" className="font-mono">
              {zone.code}
            </Badge>
          </div>
        }
      />

      <div className="flex items-center gap-2">
        <div className="flex h-9 w-9 items-center justify-center rounded-md bg-surface-sunken text-text-secondary">
          <ZoneTypeIcon zoneType={zone.zoneType} className="h-4 w-4" />
        </div>
        <Badge variant="accent">{ZONE_TYPE_LABEL[zone.zoneType]}</Badge>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Section title="Personnel" description="Who is in this zone right now.">
          <PersonnelList workers={workers} />
        </Section>

        <Section
          title="Active Permits"
          description="Permits-to-work currently in force, with their required isolation."
        >
          <PermitList permits={activePermits} />
        </Section>

        <Section title="Equipment" description="Tagged assets registered in this zone.">
          <EquipmentList equipment={equipment} />
        </Section>

        <Section
          title="Instrumentation"
          description="Live readings against each instrument's normal operating band."
        >
          <SensorList sensors={sensors} />
        </Section>
      </div>

      <Section title="Recent Activity" description="Latest logged events for this zone.">
        <ActivityList events={events ?? []} />
      </Section>

      <Section title="Coming Later" description="Modules that will connect to this zone as the platform grows.">
        <div className="grid gap-3 sm:grid-cols-2">
          {UPCOMING_CAPABILITIES.map((capability) => (
            <CapabilityPlaceholder key={capability.title} {...capability} />
          ))}
        </div>
      </Section>
    </div>
  )
}
