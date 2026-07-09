import type { CSSProperties, ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { ZoneTypeIcon, ZONE_TYPE_LABEL } from './ZoneTypeIcon'
import type { Zone } from '../types/zone'
import { Badge } from '@/components/ui/Badge'
import { cn } from '@/utils/cn'

export interface ZoneCardProps {
  zone: Zone
  to: string
  /** Reserved for a future live-status indicator (e.g. risk level). Renders nothing today. */
  statusSlot?: ReactNode
  /** Reserved for future metric badges (e.g. active sensors, open alerts). Renders nothing today. */
  metricsSlot?: ReactNode
  className?: string
  style?: CSSProperties
}

export function ZoneCard({ zone, to, statusSlot, metricsSlot, className, style }: ZoneCardProps) {
  return (
    <Link
      to={to}
      style={style}
      className={cn(
        'group flex flex-col gap-3 rounded-lg border border-border bg-surface p-4 shadow-sm transition-colors hover:border-border-strong hover:bg-surface-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent',
        className,
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-surface-sunken text-text-secondary">
          <ZoneTypeIcon zoneType={zone.zoneType} className="h-4 w-4" />
        </div>
        {statusSlot}
      </div>

      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs text-text-muted">{zone.code}</span>
          <Badge variant="neutral">{ZONE_TYPE_LABEL[zone.zoneType]}</Badge>
        </div>
        <h3 className="text-sm font-semibold text-text-primary group-hover:text-accent">
          {zone.name}
        </h3>
        <p className="line-clamp-2 text-xs text-text-secondary">{zone.description}</p>
      </div>

      {metricsSlot}
    </Link>
  )
}
