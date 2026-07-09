/**
 * Raw shapes exactly as the backend's Pydantic schemas serialize them (snake_case).
 * Never imported outside this services/ folder — everything else in the app sees the
 * camelCase domain types from ../types, mapped below.
 */

export interface RawZone {
  id: string
  code: string
  name: string
  zone_type: string
  description: string | null
  grid_row: number | null
  grid_col: number | null
}

export interface RawPlant {
  id: string
  code: string
  name: string
  city: string | null
  region: string | null
  country: string | null
}

export interface RawWorker {
  id: string
  employee_id: string
  first_name: string
  last_name: string
  role: string
  shift: string | null
  current_zone_id: string | null
}

export interface RawEquipment {
  id: string
  tag_number: string
  name: string
  equipment_type: string
  status: string
  criticality: string | null
}

export interface RawSensor {
  id: string
  tag_number: string
  sensor_type: string
  unit_of_measure: string
  status: string
  last_value: number | null
  last_reading_at: string | null
}

export interface RawPermit {
  id: string
  zone_id: string
  permit_number: string
  permit_type: string
  status: string
  description: string | null
  valid_from: string | null
  valid_until: string | null
}

export interface RawEvent {
  id: string
  event_type: string
  title: string
  description: string | null
  occurred_at: string
  zone_id: string | null
}

export interface RawZoneState {
  zone: RawZone
  workers: RawWorker[]
  equipment: RawEquipment[]
  sensors: RawSensor[]
  active_permit_count: number
}

export interface RawPlantState {
  plant: RawPlant
  generated_at: string
  zones: RawZoneState[]
  active_permits: RawPermit[]
  recent_events: RawEvent[]
}

export interface RawPage<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}
