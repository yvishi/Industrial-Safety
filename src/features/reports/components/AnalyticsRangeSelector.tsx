import { Button } from '@/components/ui/Button'
import { RANGE_PRESETS, useAnalyticsRange } from '../context/AnalyticsRangeContext'

/** The one time-range control shared by every analytics page — Shift / Today / Last 7 Days /
 * Last 30 Days, instead of separate Shift/Daily/Weekly/Monthly report implementations. */
export function AnalyticsRangeSelector() {
  const { rangeKey, setRangeKey } = useAnalyticsRange()

  return (
    <div className="flex items-center gap-2">
      {RANGE_PRESETS.map((preset) => (
        <Button
          key={preset.key}
          size="sm"
          variant={rangeKey === preset.key ? 'secondary' : 'ghost'}
          onClick={() => setRangeKey(preset.key)}
        >
          {preset.label}
        </Button>
      ))}
    </div>
  )
}
