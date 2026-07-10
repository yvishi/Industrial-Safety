import {
  Radio,
  Factory,
  FlaskConical,
  Cylinder,
  Gauge,
  Truck,
  Zap,
  Wrench,
  Flame,
  Droplets,
  type LucideIcon,
} from 'lucide-react'
import type { ZoneType } from '../types/zone'

const ZONE_TYPE_ICON: Record<ZoneType, LucideIcon> = {
  control_room: Radio,
  crude_distillation: Factory,
  vacuum_distillation: FlaskConical,
  tank_farm: Cylinder,
  pump_house: Gauge,
  loading_bay: Truck,
  utilities: Zap,
  maintenance_workshop: Wrench,
  flare_system: Flame,
  fire_water: Droplets,
}

export const ZONE_TYPE_LABEL: Record<ZoneType, string> = {
  control_room: 'Control Room',
  crude_distillation: 'Crude Distillation',
  vacuum_distillation: 'Vacuum Distillation',
  tank_farm: 'Tank Farm',
  pump_house: 'Pump House',
  loading_bay: 'Loading Bay',
  utilities: 'Utilities',
  maintenance_workshop: 'Maintenance Workshop',
  flare_system: 'Flare System',
  fire_water: 'Fire Water',
}

export interface ZoneTypeIconProps {
  zoneType: ZoneType
  className?: string
}

export function ZoneTypeIcon({ zoneType, className }: ZoneTypeIconProps) {
  const Icon = ZONE_TYPE_ICON[zoneType]
  return <Icon className={className} aria-hidden="true" />
}
