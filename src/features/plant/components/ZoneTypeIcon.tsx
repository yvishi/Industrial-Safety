import { Radio, Cog, Zap, Cylinder, Gauge, Truck, Flame, type LucideIcon } from 'lucide-react'
import type { ZoneType } from '../types/zone'

const ZONE_TYPE_ICON: Record<ZoneType, LucideIcon> = {
  'control-room': Radio,
  'processing-unit': Cog,
  utilities: Zap,
  'tank-farm': Cylinder,
  'pump-station': Gauge,
  'loading-rack': Truck,
  'flare-stack': Flame,
}

export const ZONE_TYPE_LABEL: Record<ZoneType, string> = {
  'control-room': 'Control Room',
  'processing-unit': 'Processing Unit',
  utilities: 'Utilities',
  'tank-farm': 'Tank Farm',
  'pump-station': 'Pump Station',
  'loading-rack': 'Loading Rack',
  'flare-stack': 'Flare Stack',
}

export interface ZoneTypeIconProps {
  zoneType: ZoneType
  className?: string
}

export function ZoneTypeIcon({ zoneType, className }: ZoneTypeIconProps) {
  const Icon = ZONE_TYPE_ICON[zoneType]
  return <Icon className={className} aria-hidden="true" />
}
