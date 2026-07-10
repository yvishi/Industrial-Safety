import { useState } from 'react'
import { Users } from 'lucide-react'
import { ZoneCard } from './ZoneCard'
import { ZoneSummaryModal } from './ZoneSummaryModal'
import type { Permit } from '../types/permit'
import type { ZoneState } from '../types/state'
import { useMediaQuery } from '@/hooks/useMediaQuery'

export interface ZoneGridProps {
  zones: ZoneState[]
  /** Plant-wide active permits — filtered per zone for the summary popup. */
  activePermits: Permit[]
}

/**
 * On wide viewports, zones are placed at their real `gridPosition` so the layout reads as a
 * simplified site plan rather than an arbitrary card list. Below that it falls back to a plain
 * flowing grid — the zone array is already ordered to read sensibly either way.
 */
export function ZoneGrid({ zones, activePermits }: ZoneGridProps) {
  const isSpatialLayout = useMediaQuery('(min-width: 1024px)')
  const columnCount = zones.reduce((max, { zone }) => Math.max(max, zone.gridPosition.col), 1)
  const [selectedZoneId, setSelectedZoneId] = useState<string | null>(null)

  const selectedZoneState = zones.find((entry) => entry.zone.id === selectedZoneId)

  return (
    <>
      <div
        className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"
        style={isSpatialLayout ? { gridTemplateColumns: `repeat(${columnCount}, minmax(0, 1fr))` } : undefined}
      >
        {zones.map(({ zone, workers }) => (
          <ZoneCard
            key={zone.id}
            zone={zone}
            onClick={() => setSelectedZoneId(zone.id)}
            metricsSlot={
              <div className="flex items-center gap-1.5 text-xs text-text-muted">
                <Users className="h-3.5 w-3.5" aria-hidden="true" />
                <span>
                  {workers.length} {workers.length === 1 ? 'worker' : 'workers'}
                </span>
              </div>
            }
            style={
              isSpatialLayout
                ? { gridColumn: zone.gridPosition.col, gridRow: zone.gridPosition.row }
                : undefined
            }
          />
        ))}
      </div>

      <ZoneSummaryModal
        zoneState={selectedZoneState}
        permits={activePermits.filter((permit) => permit.zoneId === selectedZoneId)}
        isOpen={selectedZoneId !== null}
        onClose={() => setSelectedZoneId(null)}
      />
    </>
  )
}
