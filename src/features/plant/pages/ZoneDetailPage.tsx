import { useParams, Link, Navigate } from 'react-router-dom'
import { ArrowLeft, Radio, Users, ShieldAlert, Wrench, ScanEye, Sparkles } from 'lucide-react'
import { PageHeader } from '@/components/ui/PageHeader'
import { Badge } from '@/components/ui/Badge'
import { Section } from '@/components/ui/Section'
import { ROUTES } from '@/app/routes'
import { getZoneById } from '../data/zones'
import { ZoneTypeIcon, ZONE_TYPE_LABEL } from '../components/ZoneTypeIcon'
import { CapabilityPlaceholder } from '../components/CapabilityPlaceholder'

const CAPABILITIES = [
  {
    icon: Radio,
    title: 'Live Sensors',
    description: 'Real-time environmental and process readings. Not yet connected.',
  },
  {
    icon: Users,
    title: 'Personnel',
    description: 'Worker presence and access tracking. Not yet connected.',
  },
  {
    icon: ShieldAlert,
    title: 'Incidents',
    description: 'Reported safety incidents for this zone. Not yet connected.',
  },
  {
    icon: Wrench,
    title: 'Maintenance',
    description: 'Scheduled and open maintenance work. Not yet connected.',
  },
  {
    icon: ScanEye,
    title: 'Computer Vision',
    description: 'Camera-based hazard and PPE detection. Not yet connected.',
  },
  {
    icon: Sparkles,
    title: 'AI Recommendations',
    description: 'Model-generated safety guidance for this zone. Not yet connected.',
  },
]

export function ZoneDetailPage() {
  const { zoneId } = useParams<{ zoneId: string }>()
  const zone = zoneId ? getZoneById(zoneId) : undefined

  if (!zone) {
    return <Navigate to={ROUTES.plant} replace />
  }

  return (
    <div className="flex flex-col gap-6">
      <Link
        to={ROUTES.plant}
        className="inline-flex w-fit items-center gap-1.5 text-sm text-text-secondary transition-colors hover:text-text-primary"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden="true" />
        Plant overview
      </Link>

      <PageHeader
        title={zone.name}
        description={zone.description}
        actions={
          <Badge variant="neutral" className="font-mono">
            {zone.code}
          </Badge>
        }
      />

      <div className="flex items-center gap-2">
        <div className="flex h-9 w-9 items-center justify-center rounded-md bg-surface-sunken text-text-secondary">
          <ZoneTypeIcon zoneType={zone.zoneType} className="h-4 w-4" />
        </div>
        <Badge variant="accent">{ZONE_TYPE_LABEL[zone.zoneType]}</Badge>
      </div>

      <Section
        title="Capabilities"
        description="Modules that will connect to this zone as the platform grows."
      >
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {CAPABILITIES.map((capability) => (
            <CapabilityPlaceholder key={capability.title} {...capability} />
          ))}
        </div>
      </Section>
    </div>
  )
}
