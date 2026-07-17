import { useState } from 'react'
import { Button } from '@/components/ui/Button'

export interface DateRange {
  since: string
  until: string
}

export interface DateRangeFilterProps {
  onChange: (range: DateRange) => void
}

interface Preset {
  label: string
  days: number
}

const PRESETS: Preset[] = [
  { label: '7 days', days: 7 },
  { label: '30 days', days: 30 },
  { label: '90 days', days: 90 },
]

const DEFAULT_PRESET_DAYS = 30

export function computeRange(days: number): DateRange {
  const until = new Date()
  const since = new Date(until.getTime() - days * 24 * 60 * 60 * 1000)
  return { since: since.toISOString(), until: until.toISOString() }
}

/** Trailing-N-days presets only — no custom date picker. Defaults to 30 days and reports the
 * initial range via onChange on mount so callers don't have to duplicate the default. */
export function DateRangeFilter({ onChange }: DateRangeFilterProps) {
  const [activeDays, setActiveDays] = useState(DEFAULT_PRESET_DAYS)

  function select(days: number) {
    setActiveDays(days)
    onChange(computeRange(days))
  }

  return (
    <div className="flex items-center gap-2">
      {PRESETS.map((preset) => (
        <Button
          key={preset.days}
          size="sm"
          variant={activeDays === preset.days ? 'secondary' : 'ghost'}
          onClick={() => select(preset.days)}
        >
          {preset.label}
        </Button>
      ))}
    </div>
  )
}

export function defaultDateRange(): DateRange {
  return computeRange(DEFAULT_PRESET_DAYS)
}
