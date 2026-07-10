import type { Equipment } from '../types/equipment'
import type { Permit } from '../types/permit'
import type { Sensor, SensorType } from '../types/sensor'
import { formatStatusLabel } from './statusMapping'

/**
 * Normal-operating-band ceilings, mirrored from the simulation engine's own warning
 * thresholds (backend/app/simulation/profiles.py) — "Normal" here means exactly what the
 * simulator itself already treats as in-band, not a separately invented judgment. If those
 * profiles change, update this table to match.
 */
const SENSOR_WARNING_LEVEL: Partial<Record<SensorType, number>> = {
  temperature: 210,
  pressure: 175,
  flow: 460,
  level: 88,
  gas_detection: 20,
  vibration: 7.1,
  smoke: 4,
}

const SENSOR_METRIC_LABEL: Record<SensorType, string> = {
  temperature: 'Temperature',
  pressure: 'Pressure',
  flow: 'Flow',
  level: 'Level',
  gas_detection: 'Gas',
  vibration: 'Vibration',
  smoke: 'Smoke',
}

const SENSOR_METRIC_ORDER: SensorType[] = [
  'gas_detection',
  'temperature',
  'pressure',
  'level',
  'flow',
  'vibration',
  'smoke',
]

export interface SensorMetricRow {
  type: SensorType
  label: string
  isElevated: boolean
}

export interface ZoneHealthSummary {
  equipmentSummary: string
  permitsSummary: string
  sensorRows: SensorMetricRow[]
  isHealthy: boolean
}

function isSensorElevated(sensor: Sensor): boolean {
  if (sensor.status === 'faulted') return true
  const warningLevel = SENSOR_WARNING_LEVEL[sensor.sensorType]
  return warningLevel !== undefined && sensor.lastValue !== null && sensor.lastValue >= warningLevel
}

function summarizeEquipment(equipment: Equipment[]): { text: string; hasConcern: boolean } {
  if (equipment.length === 0) return { text: 'None registered', hasConcern: false }

  const operational = equipment.filter((item) => item.status === 'operational').length
  const concerning = equipment.filter(
    (item) => item.status === 'under_maintenance' || item.status === 'decommissioned',
  )

  const parts = [`${operational} Operational`]
  if (concerning.length > 0) {
    parts.push(`${concerning.length} ${formatStatusLabel(concerning[0].status)}`)
  }

  return { text: parts.join(' · '), hasConcern: concerning.length > 0 }
}

function summarizePermits(permits: Permit[]): string {
  const active = permits.filter((permit) => permit.status === 'active')
  if (active.length === 0) return 'None active'
  if (active.length === 1) return `1 Active (${formatStatusLabel(active[0].permitType)})`
  return `${active.length} Active`
}

export interface SummarizeZoneHealthParams {
  equipment: Equipment[]
  permits: Permit[]
  sensors: Sensor[]
}

export function summarizeZoneHealth({
  equipment,
  permits,
  sensors,
}: SummarizeZoneHealthParams): ZoneHealthSummary {
  const { text: equipmentSummary, hasConcern } = summarizeEquipment(equipment)
  const permitsSummary = summarizePermits(permits)

  const sensorsByType = new Map<SensorType, Sensor[]>()
  for (const sensor of sensors) {
    const list = sensorsByType.get(sensor.sensorType) ?? []
    list.push(sensor)
    sensorsByType.set(sensor.sensorType, list)
  }

  const sensorRows: SensorMetricRow[] = SENSOR_METRIC_ORDER.filter((type) =>
    sensorsByType.has(type),
  ).map((type) => ({
    type,
    label: SENSOR_METRIC_LABEL[type],
    isElevated: sensorsByType.get(type)!.some(isSensorElevated),
  }))

  const anySensorElevated = sensorRows.some((row) => row.isElevated)

  return {
    equipmentSummary,
    permitsSummary,
    sensorRows,
    isHealthy: !hasConcern && !anySensorElevated,
  }
}
