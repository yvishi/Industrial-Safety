import { ZoneCard } from './ZoneCard'
import type { Zone } from '../types/zone'
import { buildZonePath } from '@/app/routes'
import { useMediaQuery } from '@/hooks/useMediaQuery'

export interface ZoneGridProps {
  zones: Zone[]
}

/**
 * On wide viewports, zones are placed at their real `gridPosition` so the layout reads as a
 * simplified site plan rather than an arbitrary card list. Below that it falls back to a plain
 * flowing grid — the zone array is already ordered to read sensibly either way.
 */
export function ZoneGrid({ zones }: ZoneGridProps) {
  const isSpatialLayout = useMediaQuery('(min-width: 1024px)')
  const columnCount = zones.reduce((max, zone) => Math.max(max, zone.gridPosition.col), 1)

  return (
    <div
      className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"
      style={isSpatialLayout ? { gridTemplateColumns: `repeat(${columnCount}, minmax(0, 1fr))` } : undefined}
    >
      {zones.map((zone) => (
        <ZoneCard
          key={zone.id}
          zone={zone}
          to={buildZonePath(zone.id)}
          style={
            isSpatialLayout
              ? { gridColumn: zone.gridPosition.col, gridRow: zone.gridPosition.row }
              : undefined
          }
        />
      ))}
    </div>
  )
}
