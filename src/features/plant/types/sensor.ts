export type SensorType =
  | 'temperature'
  | 'pressure'
  | 'flow'
  | 'level'
  | 'gas_detection'
  | 'vibration'
  | 'smoke'

export type SensorStatus = 'active' | 'inactive' | 'under_calibration' | 'faulted'

export interface Sensor {
  id: string
  tagNumber: string
  sensorType: SensorType
  unitOfMeasure: string
  status: SensorStatus
  /** Latest simulated reading, written by the backend's simulation engine. */
  lastValue: number | null
  lastReadingAt: string | null
}
