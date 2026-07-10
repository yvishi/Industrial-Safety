/** Mirrors the backend's EquipmentType enum (union across supported plant types). */
export type EquipmentType =
  | 'pump'
  | 'fire_pump'
  | 'compressor'
  | 'heat_exchanger'
  | 'fired_heater'
  | 'boiler'
  | 'distillation_column'
  | 'vessel'
  | 'tank'
  | 'control_valve'
  | 'relief_valve'
  | 'loading_arm'
  | 'flare_stack'
  | 'vacuum_ejector'
  | 'generator'
  | 'control_system'
  | 'hvac'
  | 'crane'

export type EquipmentStatus = 'operational' | 'standby' | 'under_maintenance' | 'decommissioned'

export interface Equipment {
  id: string
  tagNumber: string
  name: string
  equipmentType: EquipmentType
  status: EquipmentStatus
  criticality: string | null
}
