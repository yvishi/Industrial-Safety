export type ZoneType =
  | 'control_room'
  | 'processing_unit'
  | 'utilities'
  | 'tank_farm'
  | 'pump_station'
  | 'loading_rack'
  | 'flare_stack'

export interface GridPosition {
  row: number
  col: number
}

export interface Zone {
  id: string
  code: string
  name: string
  zoneType: ZoneType
  description: string | null
  /** Approximate physical adjacency on site, used to lay out ZoneGrid spatially on wide viewports. */
  gridPosition: GridPosition
}
