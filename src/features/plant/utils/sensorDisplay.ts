import type { Sensor, SensorType } from '../types/sensor'

/** Full instrument names for detail views (SensorList). */
export const SENSOR_TYPE_LABEL: Record<SensorType, string> = {
  temperature: 'Temperature',
  pressure: 'Pressure',
  flow: 'Flow Rate',
  level: 'Level',
  h2s: 'Hydrogen Sulfide (H₂S)',
  combustible_gas: 'Combustible Gas (LEL)',
  oxygen: 'Oxygen (O₂)',
  vibration: 'Vibration',
  valve_position: 'Valve Position',
  smoke: 'Smoke Density',
}

/** Compact names for rollup rows (zone summary modal) — hazards first in display order. */
export const SENSOR_METRIC_LABEL: Record<SensorType, string> = {
  h2s: 'H₂S',
  combustible_gas: 'LEL',
  oxygen: 'O₂',
  temperature: 'Temperature',
  pressure: 'Pressure',
  level: 'Level',
  flow: 'Flow',
  vibration: 'Vibration',
  valve_position: 'Valves',
  smoke: 'Smoke',
}

export const SENSOR_METRIC_ORDER: SensorType[] = [
  'h2s',
  'combustible_gas',
  'oxygen',
  'temperature',
  'pressure',
  'level',
  'flow',
  'vibration',
  'valve_position',
  'smoke',
]

export type SensorBand = 'normal' | 'warning' | 'critical'

/**
 * Classifies the latest reading against the instrument's own alarm bands (which the API now
 * carries per sensor). Bands are directional: H₂S alarms high, oxygen and fire-water
 * pressure alarm low. This restates the instrument's recorded thresholds — no risk scoring.
 */
export function sensorBand(sensor: Sensor): SensorBand {
  const value = sensor.lastValue
  if (value === null) return 'normal'
  if (
    (sensor.criticalMax !== null && value >= sensor.criticalMax) ||
    (sensor.criticalMin !== null && value <= sensor.criticalMin)
  ) {
    return 'critical'
  }
  if (
    (sensor.warningMax !== null && value >= sensor.warningMax) ||
    (sensor.warningMin !== null && value <= sensor.warningMin)
  ) {
    return 'warning'
  }
  return 'normal'
}

export function isSensorElevated(sensor: Sensor): boolean {
  return sensor.status === 'faulted' || sensorBand(sensor) !== 'normal'
}

/** "340–365 °C", for showing the expected operating band next to a live value. */
export function formatNormalRange(sensor: Sensor): string | null {
  if (sensor.normalMin === null || sensor.normalMax === null) return null
  return `${sensor.normalMin}–${sensor.normalMax} ${sensor.unitOfMeasure}`
}
