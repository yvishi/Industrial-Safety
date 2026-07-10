import { Link } from 'react-router-dom'
import { ArrowRight, Users } from 'lucide-react'
import { Modal } from '@/components/ui/Modal'
import { StatusPill } from '@/components/ui/StatusPill'
import { buttonVariants } from '@/components/ui/Button'
import { buildZonePath } from '@/app/routes'
import type { ZoneState } from '../types/state'
import type { Permit } from '../types/permit'
import { ZoneTypeIcon, ZONE_TYPE_LABEL } from './ZoneTypeIcon'
import { MetricRow } from './MetricRow'
import { summarizeZoneHealth } from '../utils/zoneHealth'

export interface ZoneSummaryModalProps {
  zoneState: ZoneState | undefined
  permits: Permit[]
  isOpen: boolean
  onClose: () => void
}

export function ZoneSummaryModal({ zoneState, permits, isOpen, onClose }: ZoneSummaryModalProps) {
  if (!zoneState) return null

  const { zone, workers, equipment, sensors } = zoneState
  const { equipmentSummary, permitsSummary, sensorRows, isHealthy } = summarizeZoneHealth({
    equipment,
    permits,
    sensors,
  })

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      className={isHealthy ? 'border-t-4 border-t-success' : 'border-t-4 border-t-warning'}
      title={
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-surface-sunken text-text-secondary">
            <ZoneTypeIcon zoneType={zone.zoneType} className="h-4 w-4" />
          </div>
          <span>{zone.name}</span>
        </div>
      }
      description={
        <span className="font-mono">
          {zone.code} · {ZONE_TYPE_LABEL[zone.zoneType]}
        </span>
      }
      footer={
        <Link
          to={buildZonePath(zone.id)}
          onClick={onClose}
          className={buttonVariants({ variant: 'primary', size: 'md', className: 'w-full' })}
        >
          View Full Report
          <ArrowRight className="h-4 w-4" aria-hidden="true" />
        </Link>
      }
    >
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between gap-3 rounded-lg bg-surface-sunken px-4 py-3">
          <span className="text-sm font-medium text-text-primary">Zone Status</span>
          <StatusPill
            status={isHealthy ? 'operational' : 'warning'}
            label={isHealthy ? 'Operational' : 'Attention Needed'}
          />
        </div>

        <dl className="flex flex-col divide-y divide-border">
          <MetricRow
            label="Workers"
            value={
              <span className="inline-flex items-center gap-1.5">
                <Users className="h-3.5 w-3.5 text-text-muted" aria-hidden="true" />
                {workers.length}
              </span>
            }
          />
          <MetricRow label="Equipment" value={equipmentSummary} />
          <MetricRow label="Permits" value={permitsSummary} />
          {sensorRows.map((row) => (
            <MetricRow
              key={row.type}
              label={row.label}
              value={
                <span className={row.isElevated ? 'text-warning' : undefined}>
                  {row.isElevated ? 'Elevated' : 'Normal'}
                </span>
              }
            />
          ))}
        </dl>

        <div className="flex items-center justify-between gap-3 border-t border-border pt-3">
          <span className="text-sm font-medium text-text-primary">Overall Health</span>
          <StatusPill
            status={isHealthy ? 'operational' : 'warning'}
            label={isHealthy ? 'Healthy' : 'Needs Attention'}
          />
        </div>
      </div>
    </Modal>
  )
}
