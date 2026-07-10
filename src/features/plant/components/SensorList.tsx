import { StatusPill } from '@/components/ui/StatusPill'
import type { Sensor } from '../types/sensor'
import { formatStatusLabel, sensorStatusPill } from '../utils/statusMapping'
import { SENSOR_TYPE_LABEL, formatNormalRange, sensorBand } from '../utils/sensorDisplay'
import { cn } from '@/utils/cn'

export interface SensorListProps {
  sensors: Sensor[]
}

export function SensorList({ sensors }: SensorListProps) {
  if (sensors.length === 0) {
    return <p className="text-sm text-text-muted">No instruments registered in this zone.</p>
  }

  return (
    <ul className="flex flex-col divide-y divide-border rounded-lg border border-border">
      {sensors.map((sensor) => {
        const band = sensorBand(sensor)
        const normalRange = formatNormalRange(sensor)
        return (
          <li key={sensor.id} className="flex flex-wrap items-center justify-between gap-x-3 gap-y-2 px-4 py-3">
            <div className="flex min-w-0 flex-1 flex-col">
              <span className="truncate text-sm font-medium text-text-primary">
                {SENSOR_TYPE_LABEL[sensor.sensorType] ?? formatStatusLabel(sensor.sensorType)}
              </span>
              <span className="font-mono text-xs text-text-muted">
                {sensor.tagNumber}
                {normalRange ? ` · Normal ${normalRange}` : ''}
              </span>
            </div>
            <div className="flex shrink-0 items-center gap-3">
              {sensor.lastValue !== null && (
                <span
                  className={cn(
                    'font-mono text-sm',
                    band === 'critical' && 'font-semibold text-danger',
                    band === 'warning' && 'font-semibold text-warning',
                    band === 'normal' && 'text-text-primary',
                  )}
                >
                  {sensor.lastValue.toFixed(1)} {sensor.unitOfMeasure}
                </span>
              )}
              <StatusPill status={sensorStatusPill(sensor.status)} label={formatStatusLabel(sensor.status)} />
            </div>
          </li>
        )
      })}
    </ul>
  )
}
