import type { Equipment } from './equipment'
import type { PlantEvent } from './event'
import type { Permit } from './permit'
import type { PlantProfile } from './plant'
import type { Sensor } from './sensor'
import type { Worker } from './worker'
import type { Zone } from './zone'

export interface ZoneState {
  zone: Zone
  workers: Worker[]
  equipment: Equipment[]
  sensors: Sensor[]
  activePermitCount: number
}

/** The aggregate live snapshot the frontend polls — mirrors GET /api/v1/state. */
export interface PlantState {
  plant: PlantProfile
  generatedAt: string
  zones: ZoneState[]
  activePermits: Permit[]
  recentEvents: PlantEvent[]
}
