import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'

export type AnalyticsRangeKey = 'shift' | 'today' | '7d' | '30d'

export interface AnalyticsRange {
  key: AnalyticsRangeKey
  since: string
  until: string
  label: string
}

const SHIFT_HOURS = 8
export const DEFAULT_RANGE_KEY: AnalyticsRangeKey = '30d'

export const RANGE_PRESETS: Array<{ key: AnalyticsRangeKey; label: string }> = [
  { key: 'shift', label: 'Shift' },
  { key: 'today', label: 'Today' },
  { key: '7d', label: 'Last 7 Days' },
  { key: '30d', label: 'Last 30 Days' },
]

/** The one place every analytics page/report derives its window from — a single time-range
 * system instead of separate Shift/Daily/Weekly/Monthly report implementations. */
export function computeAnalyticsRange(key: AnalyticsRangeKey): AnalyticsRange {
  const until = new Date()
  let since: Date
  let label: string

  switch (key) {
    case 'shift':
      since = new Date(until.getTime() - SHIFT_HOURS * 60 * 60 * 1000)
      label = 'Current Shift (8h)'
      break
    case 'today':
      since = new Date(until.getFullYear(), until.getMonth(), until.getDate())
      label = 'Today'
      break
    case '7d':
      since = new Date(until.getTime() - 7 * 24 * 60 * 60 * 1000)
      label = 'Last 7 Days'
      break
    case '30d':
      since = new Date(until.getTime() - 30 * 24 * 60 * 60 * 1000)
      label = 'Last 30 Days'
      break
  }

  return { key, since: since.toISOString(), until: until.toISOString(), label }
}

interface AnalyticsRangeContextValue {
  rangeKey: AnalyticsRangeKey
  range: AnalyticsRange
  setRangeKey: (key: AnalyticsRangeKey) => void
}

const AnalyticsRangeContext = createContext<AnalyticsRangeContextValue | null>(null)

/** Wraps every analytics page (Safety Trend / Zones & Hazards / Incident Response) so switching
 * the time range in one place updates all of them — no per-page filter state, no duplicated
 * Shift/Daily/Weekly/Monthly report logic. */
export function AnalyticsRangeProvider({ children }: { children: ReactNode }) {
  const [rangeKey, setRangeKey] = useState<AnalyticsRangeKey>(DEFAULT_RANGE_KEY)
  const range = useMemo(() => computeAnalyticsRange(rangeKey), [rangeKey])

  return (
    <AnalyticsRangeContext.Provider value={{ rangeKey, range, setRangeKey }}>
      {children}
    </AnalyticsRangeContext.Provider>
  )
}

export function useAnalyticsRange(): AnalyticsRangeContextValue {
  const ctx = useContext(AnalyticsRangeContext)
  if (!ctx) throw new Error('useAnalyticsRange must be used within an AnalyticsRangeProvider')
  return ctx
}
