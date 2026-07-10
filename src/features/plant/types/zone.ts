/** Industry-specific zone identity — mirrors the backend's ZoneType enum (union across supported plant types). */
export type ZoneType =
  | 'control_room'
  | 'crude_distillation'
  | 'vacuum_distillation'
  | 'tank_farm'
  | 'pump_house'
  | 'loading_bay'
  | 'utilities'
  | 'maintenance_workshop'
  | 'flare_system'
  | 'fire_water'

/** Coarse cross-industry grouping; the fine-grained identity lives in ZoneType. */
export type ZoneCategory =
  | 'process'
  | 'storage'
  | 'product_movement'
  | 'utilities'
  | 'safety_systems'
  | 'support'

export interface GridPosition {
  row: number
  col: number
}

export interface Zone {
  id: string
  code: string
  name: string
  zoneType: ZoneType
  zoneCategory: ZoneCategory
  description: string | null
  /** Approximate physical adjacency on site, used to lay out ZoneGrid spatially on wide viewports. */
  gridPosition: GridPosition
}
