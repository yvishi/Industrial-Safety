import { Radio, Cog, Zap, Cylinder, Gauge, Truck, Flame, type LucideIcon } from 'lucide-react'
import type { ZoneType } from '../types/zone'

const ZONE_TYPE_ICON: Record<ZoneType, LucideIcon> = {
  control_room: Radio,
  processing_unit: Cog,
  utilities: Zap,
  tank_farm: Cylinder,
  pump_station: Gauge,
  loading_rack: Truck,
  flare_stack: Flame,
}

export const ZONE_TYPE_LABEL: Record<ZoneType, string> = {
  control_room: 'Control Room',
  processing_unit: 'Processing Unit',
  utilities: 'Utilities',
  tank_farm: 'Tank Farm',
  pump_station: 'Pump Station',
  loading_rack: 'Loading Rack',
  flare_stack: 'Flare Stack',
}

export interface ZoneTypeIconProps {
  zoneType: ZoneType
  className?: string
}

export function ZoneTypeIcon({ zoneType, className }: ZoneTypeIconProps) {
  const Icon = ZONE_TYPE_ICON[zoneType]
  return <Icon className={className} aria-hidden="true" />
}
