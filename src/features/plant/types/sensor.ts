/** Real industrial measurement types — mirrors the backend's SensorType enum. */
export type SensorType =
  | 'temperature'
  | 'pressure'
  | 'flow'
  | 'level'
  | 'h2s'
  | 'combustible_gas'
  | 'oxygen'
  | 'vibration'
  | 'valve_position'
  | 'smoke'

export type SensorStatus = 'active' | 'inactive' | 'under_calibration' | 'faulted'

export interface Sensor {
  id: string
  tagNumber: string
  sensorType: SensorType
  unitOfMeasure: string
  status: SensorStatus
  /**
   * Alarm bands for this installed instrument, in unitOfMeasure. Nullable per side because
   * hazards are directional: H₂S alarms high, oxygen and fire-water pressure alarm low.
   */
  normalMin: number | null
  normalMax: number | null
  warningMin: number | null
  warningMax: number | null
  criticalMin: number | null
  criticalMax: number | null
  samplingIntervalSeconds: number
  /** Latest simulated reading, written by the backend's simulation engine. */
  lastValue: number | null
  lastReadingAt: string | null
}
