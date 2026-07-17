import type { LucideIcon } from 'lucide-react'
import { cn } from '@/utils/cn'

export type ReportKpiTone = 'neutral' | 'success' | 'warning' | 'danger'

export interface ReportKpiTileProps {
  label: string
  value: string | number
  sublabel?: string
  icon: LucideIcon
  tone?: ReportKpiTone
}

const VALUE_TONE_CLASS: Record<ReportKpiTone, string> = {
  neutral: 'text-text-primary',
  success: 'text-success',
  warning: 'text-warning',
  danger: 'text-danger',
}

const ICON_TONE_CLASS: Record<ReportKpiTone, string> = {
  neutral: 'text-text-muted',
  success: 'text-success',
  warning: 'text-warning',
  danger: 'text-danger',
}

/** Generic stat tile shared by every report page — same quiet-card shape as the Dashboard's
 * KPI row (see DashboardKpiRow's TILE_CLASS), just not link-wrapped since these summarize
 * historical data rather than pointing at a live record. */
export function ReportKpiTile({ label, value, sublabel, icon: Icon, tone = 'neutral' }: ReportKpiTileProps) {
  return (
    <div className="flex flex-col gap-2 rounded-lg border border-border bg-surface p-5">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wide text-text-muted">{label}</span>
        <Icon className={cn('h-4 w-4', ICON_TONE_CLASS[tone])} aria-hidden="true" />
      </div>
      <span className={cn('text-3xl font-semibold', VALUE_TONE_CLASS[tone])}>{value}</span>
      {sublabel && <span className="text-xs text-text-secondary">{sublabel}</span>}
    </div>
  )
}
