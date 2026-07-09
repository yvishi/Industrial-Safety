export type EquipmentType =
  | 'pump'
  | 'compressor'
  | 'heat_exchanger'
  | 'vessel'
  | 'tank'
  | 'valve'
  | 'reactor'
  | 'furnace'
  | 'instrument'

export type EquipmentStatus = 'operational' | 'standby' | 'under_maintenance' | 'decommissioned'

export interface Equipment {
  id: string
  tagNumber: string
  name: string
  equipmentType: EquipmentType
  status: EquipmentStatus
  criticality: string | null
}
