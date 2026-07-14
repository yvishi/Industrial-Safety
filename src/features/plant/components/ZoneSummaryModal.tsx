import { Link } from 'react-router-dom'
import { ArrowRight, TriangleAlert, Users } from 'lucide-react'
import { Modal } from '@/components/ui/Modal'
import { StatusPill } from '@/components/ui/StatusPill'
import { buttonVariants } from '@/components/ui/Button'
import { buildZonePath } from '@/app/routes'
import { usePolling } from '@/hooks/usePolling'
import type { ZoneState } from '../types/state'
import type { Permit } from '../types/permit'
import type { RiskAssessment } from '../types/risk'
import { fetchZoneRecommendations } from '../services/recommendationService'
import { ZoneTypeIcon, ZONE_TYPE_LABEL } from './ZoneTypeIcon'
import { MetricRow } from './MetricRow'
import { summarizeZoneHealth } from '../utils/zoneHealth'
import { RISK_LEVEL_BORDER_CLASS, RISK_LEVEL_LABEL, riskLevelStatus } from '../utils/riskDisplay'

const POLL_INTERVAL_MS = 5000

export interface ZoneSummaryModalProps {
  zoneState: ZoneState | undefined
  permits: Permit[]
  /** Live Compound Risk Engine assessment for this zone — undefined while still loading, in
   * which case the modal falls back to the raw operational health check below. */
  riskAssessment: RiskAssessment | undefined
  isOpen: boolean
  onClose: () => void
}

export function ZoneSummaryModal({ zoneState, permits, riskAssessment, isOpen, onClose }: ZoneSummaryModalProps) {
  const { data: recommendations } = usePolling(
    () => (isOpen && zoneState ? fetchZoneRecommendations(zoneState.zone.id) : Promise.resolve([])),
    POLL_INTERVAL_MS,
  )

  if (!zoneState) return null

  const { zone, workers, equipment, sensors } = zoneState
  const activeRecommendationCount = recommendations?.length ?? 0
  const criticalRecommendationCount = recommendations?.filter((r) => r.priority === 'critical').length ?? 0
  const { equipmentSummary, permitsSummary, sensorRows, isHealthy } = summarizeZoneHealth({
    equipment,
    permits,
    sensors,
  })

  const borderClass = riskAssessment
    ? RISK_LEVEL_BORDER_CLASS[riskAssessment.level]
    : isHealthy
      ? 'border-t-success'
      : 'border-t-warning'
  const statusPillProps = riskAssessment
    ? { status: riskLevelStatus(riskAssessment.level), label: RISK_LEVEL_LABEL[riskAssessment.level] }
    : { status: isHealthy ? ('operational' as const) : ('warning' as const), label: isHealthy ? 'Operational' : 'Attention Needed' }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      className={`border-t-4 ${borderClass}`}
      title={
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-surface-sunken text-text-secondary">
            <ZoneTypeIcon zoneType={zone.zoneType} className="h-4 w-4" />
          </div>
          <span>{zone.name}</span>
        </div>
      }
      description={
        <span className="font-mono">
          {zone.code} · {ZONE_TYPE_LABEL[zone.zoneType]}
        </span>
      }
      footer={
        <Link
          to={buildZonePath(zone.id)}
          onClick={onClose}
          className={buttonVariants({ variant: 'primary', size: 'md', className: 'w-full' })}
        >
          View Full Report
          <ArrowRight className="h-4 w-4" aria-hidden="true" />
        </Link>
      }
    >
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between gap-3 rounded-lg bg-surface-sunken px-4 py-3">
          <span className="text-sm font-medium text-text-primary">Risk Level</span>
          <div className="flex items-center gap-2">
            {riskAssessment && (
              <span className="font-mono text-xs text-text-muted">{riskAssessment.score}/100</span>
            )}
            <StatusPill status={statusPillProps.status} label={statusPillProps.label} />
          </div>
        </div>

        <dl className="flex flex-col divide-y divide-border">
          <MetricRow
            label="Workers"
            value={
              <span className="inline-flex items-center gap-1.5">
                <Users className="h-3.5 w-3.5 text-text-muted" aria-hidden="true" />
                {workers.length}
              </span>
            }
          />
          <MetricRow label="Equipment" value={equipmentSummary} />
          <MetricRow label="Permits" value={permitsSummary} />
          {sensorRows.map((row) => (
            <MetricRow
              key={row.type}
              label={row.label}
              value={
                <span className={row.isElevated ? 'text-warning' : undefined}>
                  {row.isElevated ? 'Elevated' : 'Normal'}
                </span>
              }
            />
          ))}
        </dl>

        {riskAssessment && (
          <div className="flex flex-col gap-2 border-t border-border pt-3">
            <span className="text-sm font-medium text-text-primary">Compound Risk Engine</span>
            <p className="text-xs text-text-secondary">{riskAssessment.explanation}</p>
            {riskAssessment.contributors.length > 0 && (
              <ul className="flex flex-col gap-1.5">
                {riskAssessment.contributors.slice(0, 3).map((contributor) => (
                  <li key={contributor.ruleId} className="flex items-center justify-between gap-3 text-xs">
                    <span className="text-text-secondary">{contributor.factor}</span>
                    <span className="font-mono text-text-muted">+{contributor.impact}</span>
                  </li>
                ))}
              </ul>
            )}
            <span className="text-xs text-text-muted">
              Confidence: {riskAssessment.confidenceLabel} · {riskAssessment.engineVersion}
            </span>
          </div>
        )}

        {activeRecommendationCount > 0 && (
          <div className="flex items-center gap-2 rounded-lg bg-danger-subtle px-3 py-2 text-xs text-danger">
            <TriangleAlert className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
            <span>
              {activeRecommendationCount} active {activeRecommendationCount === 1 ? 'recommendation' : 'recommendations'}
              {criticalRecommendationCount > 0 &&
                ` (${criticalRecommendationCount} critical)`}
            </span>
          </div>
        )}
      </div>
    </Modal>
  )
}
