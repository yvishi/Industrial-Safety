export type ZoneType =
  | 'control-room'
  | 'processing-unit'
  | 'utilities'
  | 'tank-farm'
  | 'pump-station'
  | 'loading-rack'
  | 'flare-stack'

export interface GridPosition {
  row: number
  col: number
}

export interface Zone {
  id: string
  code: string
  name: string
  zoneType: ZoneType
  description: string
  /** Approximate physical adjacency on site, used to lay out ZoneGrid spatially on wide viewports. */
  gridPosition: GridPosition
}
