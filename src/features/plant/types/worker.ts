export type WorkerRole =
  | 'plant_manager'
  | 'safety_officer'
  | 'shift_supervisor'
  | 'operations_director'
  | 'process_operator'
  | 'maintenance_technician'
  | 'contractor'

export type Shift = 'day' | 'night' | 'swing'

export interface Worker {
  id: string
  employeeId: string
  firstName: string
  lastName: string
  role: WorkerRole
  shift: Shift | null
  currentZoneId: string | null
}
