import type { Status } from '@/types/common'
import type { RiskCategoryKey, TrendDirection } from '@/features/plant/types/risk'
import type { PeriodGranularity } from '../types/reports'

export const RISK_CATEGORY_LABEL: Record<RiskCategoryKey, string> = {
  gas_hazard: 'Gas Hazard',
  fire_explosion: 'Fire & Explosion',
  equipment: 'Equipment',
  personnel_exposure: 'Personnel Exposure',
  permit_compliance: 'Permit Compliance',
  environmental: 'Environmental',
  process_safety: 'Process Safety',
}

/** Incident volume trend -> Status. Unlike a conventional metric, "up" here means
 * incident volume is RISING (worse) and "down" means it's FALLING (better) — this is a
 * safety-incident count, not revenue, so the usual up=green intuition is inverted. */
export function trendDirectionStatus(direction: TrendDirection): Status {
  switch (direction) {
    case 'up':
      return 'critical'
    case 'down':
      return 'operational'
    case 'flat':
      return 'info'
  }
}

export function trendDirectionLabel(direction: TrendDirection): string {
  switch (direction) {
    case 'up':
      return 'Worsening'
    case 'down':
      return 'Improving'
    case 'flat':
      return 'Stable'
  }
}

/** Renders an em dash for null/undefined instead of "0h" or "NaNh". */
export function formatHours(hours: number | null | undefined): string {
  if (hours === null || hours === undefined) return '—'
  return `${hours.toFixed(1)}h`
}

/** Renders an em dash for null/undefined instead of "0m" or "NaNm". */
export function formatMinutes(minutes: number | null | undefined): string {
  if (minutes === null || minutes === undefined) return '—'
  return `${minutes.toFixed(1)}m`
}

/** Chart x-axis label for one period, shaped by its granularity — "Jun 17" for day/week,
 * "Jun 2026" for month. */
export function formatPeriodLabel(periodStart: string, granularity: PeriodGranularity): string {
  const date = new Date(periodStart)
  if (granularity === 'month') {
    return date.toLocaleDateString(undefined, { month: 'short', year: 'numeric' })
  }
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}
