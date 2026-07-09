import type { Equipment, EquipmentStatus, EquipmentType } from '../types/equipment'
import type { PlantEvent } from '../types/event'
import type { PlantProfile } from '../types/plant'
import type { Permit, PermitStatus, PermitType } from '../types/permit'
import type { Sensor, SensorStatus, SensorType } from '../types/sensor'
import type { Shift, Worker, WorkerRole } from '../types/worker'
import type { Zone, ZoneType } from '../types/zone'
import type {
  RawEquipment,
  RawEvent,
  RawPermit,
  RawPlant,
  RawSensor,
  RawWorker,
  RawZone,
} from './wireTypes'

export function mapPlant(raw: RawPlant): PlantProfile {
  return {
    name: raw.name,
    code: raw.code,
    location: [raw.city, raw.region].filter(Boolean).join(', ') || (raw.country ?? ''),
  }
}

export function mapZone(raw: RawZone): Zone {
  return {
    id: raw.id,
    code: raw.code,
    name: raw.name,
    zoneType: raw.zone_type as ZoneType,
    description: raw.description,
    gridPosition: { row: raw.grid_row ?? 0, col: raw.grid_col ?? 0 },
  }
}

export function mapWorker(raw: RawWorker): Worker {
  return {
    id: raw.id,
    employeeId: raw.employee_id,
    firstName: raw.first_name,
    lastName: raw.last_name,
    role: raw.role as WorkerRole,
    shift: raw.shift as Shift | null,
    currentZoneId: raw.current_zone_id,
  }
}

export function mapEquipment(raw: RawEquipment): Equipment {
  return {
    id: raw.id,
    tagNumber: raw.tag_number,
    name: raw.name,
    equipmentType: raw.equipment_type as EquipmentType,
    status: raw.status as EquipmentStatus,
    criticality: raw.criticality,
  }
}

export function mapSensor(raw: RawSensor): Sensor {
  return {
    id: raw.id,
    tagNumber: raw.tag_number,
    sensorType: raw.sensor_type as SensorType,
    unitOfMeasure: raw.unit_of_measure,
    status: raw.status as SensorStatus,
    lastValue: raw.last_value,
    lastReadingAt: raw.last_reading_at,
  }
}

export function mapPermit(raw: RawPermit): Permit {
  return {
    id: raw.id,
    zoneId: raw.zone_id,
    permitNumber: raw.permit_number,
    permitType: raw.permit_type as PermitType,
    status: raw.status as PermitStatus,
    description: raw.description,
    validFrom: raw.valid_from,
    validUntil: raw.valid_until,
  }
}

export function mapEvent(raw: RawEvent): PlantEvent {
  return {
    id: raw.id,
    eventType: raw.event_type,
    title: raw.title,
    description: raw.description,
    occurredAt: raw.occurred_at,
    zoneId: raw.zone_id,
  }
}
