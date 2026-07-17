import { Link } from 'react-router-dom'
import { ClipboardList, ShieldAlert, ShieldCheck } from 'lucide-react'
import { ROUTES, buildZonePath } from '@/app/routes'
import { StatusPill } from '@/components/ui/StatusPill'
import { RISK_LEVEL_LABEL, riskLevelStatus } from '@/features/plant/utils/riskDisplay'
import type { RiskLevel } from '@/features/plant/types/risk'
import { cn } from '@/utils/cn'

export interface DashboardKpiRowProps {
  openIncidentCount: number
  urgentIncidentCount: number
  mostCriticalZone: { zoneId: string; zoneName: string; level: RiskLevel; score: number } | null
}

const TILE_CLASS =
  'rounded-lg border border-border bg-surface p-5 flex flex-col gap-2 transition-colors hover:border-border-strong hover:bg-surface-hover'

const LABEL_CLASS = 'flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-text-muted'

export function DashboardKpiRow({
  openIncidentCount,
  urgentIncidentCount,
  mostCriticalZone,
}: DashboardKpiRowProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-3">
      <Link to={ROUTES.incidents} className={TILE_CLASS}>
        <span className="text-3xl font-semibold text-text-primary">{openIncidentCount}</span>
        <span className={LABEL_CLASS}>
          <ClipboardList className="h-3.5 w-3.5" aria-hidden="true" />
          Open Incidents
        </span>
      </Link>

      {mostCriticalZone ? (
        <Link to={buildZonePath(mostCriticalZone.zoneId)} className={TILE_CLASS}>
          <span className="text-lg font-semibold text-text-primary">{mostCriticalZone.zoneName}</span>
          <StatusPill
            status={riskLevelStatus(mostCriticalZone.level)}
            label={RISK_LEVEL_LABEL[mostCriticalZone.level]}
          />
          <span className="text-xs text-text-muted">Risk score {mostCriticalZone.score}</span>
          <span className={LABEL_CLASS}>Most Critical Zone</span>
        </Link>
      ) : (
        <div className={cn(TILE_CLASS, 'hover:border-border hover:bg-surface')}>
          <span className="text-lg font-semibold text-text-muted">No zone data</span>
          <span className={LABEL_CLASS}>Most Critical Zone</span>
        </div>
      )}

      <Link to={ROUTES.incidents} className={TILE_CLASS}>
        <span
          className={cn(
            'text-3xl font-semibold',
            urgentIncidentCount > 0 ? 'text-danger' : 'text-success',
          )}
        >
          {urgentIncidentCount}
        </span>
        <span className={LABEL_CLASS}>
          {urgentIncidentCount > 0 ? (
            <ShieldAlert className="h-3.5 w-3.5" aria-hidden="true" />
          ) : (
            <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
          )}
          Needs Immediate Action
        </span>
      </Link>
    </div>
  )
}
