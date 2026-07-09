import { PageHeader } from '@/components/ui/PageHeader'
import { Badge } from '@/components/ui/Badge'
import { ZoneGrid } from '../components/ZoneGrid'
import { getZones } from '../data/zones'
import { getPlantProfile } from '../data/plant'

export function PlantOverviewPage() {
  const zones = getZones()
  const plant = getPlantProfile()

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title={plant.name}
        description={`${plant.location} — ${zones.length} zones`}
        actions={
          <Badge variant="neutral" className="font-mono">
            {plant.code}
          </Badge>
        }
      />
      <ZoneGrid zones={zones} />
    </div>
  )
}
