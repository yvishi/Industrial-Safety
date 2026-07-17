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

/** Renders an em dash for null/undefined. Below 60 minutes, shows minutes ("18 min") instead
 * of flattening a fast resolution to a meaningless "0.0h" — realistic for simulated/short
 * response times, not just long-running ones. */
export function formatHours(hours: number | null | undefined): string {
  if (hours === null || hours === undefined) return '—'
  if (hours < 1) {
    const minutes = Math.round(hours * 60)
    return minutes < 1 ? '< 1 min' : `${minutes} min`
  }
  return `${hours.toFixed(1)}h`
}

/** Same rule as formatHours, for values that arrive in minutes (e.g. time-to-acknowledge):
 * below 60 minutes shows minutes, otherwise converts to hours. */
export function formatMinutes(minutes: number | null | undefined): string {
  if (minutes === null || minutes === undefined) return '—'
  if (minutes < 60) {
    const rounded = Math.round(minutes)
    return rounded < 1 ? '< 1 min' : `${rounded} min`
  }
  return `${(minutes / 60).toFixed(1)}h`
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

/** "Jun 17, 2026, 3:04 PM – Jul 17, 2026, 3:04 PM" — the exact window a report/analytics page
 * covers, for display under a range label like "Last 30 Days". */
export function formatDateRange(since: string, until: string): string {
  const format = (iso: string) =>
    new Date(iso).toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    })
  return `${format(since)} – ${format(until)}`
}
