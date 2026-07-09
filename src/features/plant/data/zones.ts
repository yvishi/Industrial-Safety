import type { Zone } from '../types/zone'

/**
 * Static structural data for Phase 1 — zone identity and layout only, no live/operational state.
 * `gridPosition` approximates real adjacency on site (e.g. the flare stack sits isolated at the
 * perimeter, away from loading and control areas, per standard process-safety siting practice).
 * Replace with a real service call once a backend exists; callers only depend on this signature.
 */
const ZONES: Zone[] = [
  {
    id: 'cr-01',
    code: 'CR-01',
    name: 'Central Control Room',
    zoneType: 'control-room',
    description: 'Centralized monitoring and process control for all site operations.',
    gridPosition: { row: 1, col: 1 },
  },
  {
    id: 'pu-01',
    code: 'PU-01',
    name: 'Crude Distillation Unit',
    zoneType: 'processing-unit',
    description: 'Atmospheric distillation and primary hydrocarbon separation.',
    gridPosition: { row: 1, col: 2 },
  },
  {
    id: 'pu-02',
    code: 'PU-02',
    name: 'Catalytic Reformer Unit',
    zoneType: 'processing-unit',
    description: 'Converts naphtha into high-octane reformate via catalytic reforming.',
    gridPosition: { row: 1, col: 3 },
  },
  {
    id: 'ut-01',
    code: 'UT-01',
    name: 'Utilities & Steam Plant',
    zoneType: 'utilities',
    description: 'Steam generation, compressed air, and site-wide power distribution.',
    gridPosition: { row: 1, col: 4 },
  },
  {
    id: 'tf-01',
    code: 'TF-01',
    name: 'Tank Farm',
    zoneType: 'tank-farm',
    description: 'Bulk storage for crude feedstock and finished petroleum products.',
    gridPosition: { row: 2, col: 1 },
  },
  {
    id: 'ps-01',
    code: 'PS-01',
    name: 'Pump Station',
    zoneType: 'pump-station',
    description: 'Transfer pumping between storage, process units, and loading systems.',
    gridPosition: { row: 2, col: 2 },
  },
  {
    id: 'lr-01',
    code: 'LR-01',
    name: 'Loading Rack',
    zoneType: 'loading-rack',
    description: 'Truck and rail loading for finished product distribution.',
    gridPosition: { row: 2, col: 3 },
  },
  {
    id: 'fs-01',
    code: 'FS-01',
    name: 'Flare Stack',
    zoneType: 'flare-stack',
    description: 'Emergency pressure relief and combustion of process off-gases.',
    gridPosition: { row: 2, col: 4 },
  },
]

export function getZones(): Zone[] {
  return ZONES
}

export function getZoneById(zoneId: string): Zone | undefined {
  return ZONES.find((zone) => zone.id === zoneId)
}
