import { Link } from 'react-router-dom'
import { AlertTriangle, Check, CircleCheck, FileText, Gauge, MapPin, Wrench } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { buildZonePath } from '@/app/routes'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { StatusPill } from '@/components/ui/StatusPill'
import { cn } from '@/utils/cn'
import type { Recommendation } from '../types/recommendation'
import {
  RECOMMENDATION_PRIORITY_LABEL,
  RECOMMENDATION_STATE_LABEL,
  recommendationPriorityStatus,
} from '../utils/recommendationDisplay'

const TARGET_ICON: Record<string, LucideIcon> = {
  zone: MapPin,
  sensor: Gauge,
  equipment: Wrench,
  permit: FileText,
}

export interface RecommendationCardProps {
  recommendation: Recommendation
  /** The single most urgent item on a page renders as a command, not a checklist row. */
  emphasized?: boolean
  /** Shown on the plant-wide Action Queue, where a card can come from any zone. */
  showZoneLabel?: boolean
  onAcknowledge: () => void
  onResolve: () => void
  isPending?: boolean
}

export function RecommendationCard({
  recommendation,
  emphasized = false,
  showZoneLabel = false,
  onAcknowledge,
  onResolve,
  isPending = false,
}: RecommendationCardProps) {
  const TargetIcon = TARGET_ICON[recommendation.targetEntity.entityType] ?? MapPin
  const isNew = recommendation.state === 'new'

  if (emphasized) {
    return (
      <div className="flex flex-col gap-4 rounded-lg border border-danger/30 bg-danger-subtle p-5">
        <div className="flex items-center gap-2 text-danger">
          <AlertTriangle className="h-4 w-4" aria-hidden="true" />
          <span className="text-xs font-semibold uppercase tracking-wider">Action Required</span>
          {showZoneLabel && (
            <Link
              to={buildZonePath(recommendation.zoneId)}
              className="ml-auto text-xs font-medium text-text-secondary underline-offset-2 hover:text-text-primary hover:underline"
            >
              {recommendation.zoneName}
            </Link>
          )}
        </div>

        <div className="flex flex-col gap-1.5">
          <h3 className="text-lg font-semibold text-text-primary">{recommendation.title}</h3>
          <p className="text-sm text-text-secondary">{recommendation.actionText}</p>
        </div>

        <RecommendationMeta recommendation={recommendation} TargetIcon={TargetIcon} />

        <div className="flex items-center gap-2 pt-1">
          {isNew && (
            <Button variant="destructive" size="sm" onClick={onAcknowledge} isLoading={isPending}>
              <Check className="h-3.5 w-3.5" aria-hidden="true" />
              Acknowledge
            </Button>
          )}
          <Button variant="outline" size="sm" onClick={onResolve} isLoading={isPending}>
            <CircleCheck className="h-3.5 w-3.5" aria-hidden="true" />
            Mark Resolved
          </Button>
          {!isNew && <StatusPill status="warning" label={RECOMMENDATION_STATE_LABEL[recommendation.state]} className="ml-auto" />}
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-3 rounded-lg border border-border p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <StatusPill
              status={recommendationPriorityStatus(recommendation.priority)}
              label={RECOMMENDATION_PRIORITY_LABEL[recommendation.priority]}
            />
            {showZoneLabel && (
              <Link
                to={buildZonePath(recommendation.zoneId)}
                className="text-xs text-text-muted underline-offset-2 hover:text-text-primary hover:underline"
              >
                {recommendation.zoneName}
              </Link>
            )}
          </div>
          <p className="text-sm font-medium text-text-primary">{recommendation.title}</p>
          <p className="text-xs text-text-secondary">{recommendation.actionText}</p>
        </div>
        {recommendation.state === 'acknowledged' && (
          <Badge variant="neutral">{RECOMMENDATION_STATE_LABEL[recommendation.state]}</Badge>
        )}
      </div>

      <RecommendationMeta recommendation={recommendation} TargetIcon={TargetIcon} compact />

      <div className="flex items-center gap-2">
        {isNew && (
          <Button variant="secondary" size="sm" onClick={onAcknowledge} isLoading={isPending}>
            <Check className="h-3.5 w-3.5" aria-hidden="true" />
            Acknowledge
          </Button>
        )}
        <Button variant="ghost" size="sm" onClick={onResolve} isLoading={isPending}>
          <CircleCheck className="h-3.5 w-3.5" aria-hidden="true" />
          Mark Resolved
        </Button>
      </div>
    </div>
  )
}

function RecommendationMeta({
  recommendation,
  TargetIcon,
  compact = false,
}: {
  recommendation: Recommendation
  TargetIcon: LucideIcon
  compact?: boolean
}) {
  return (
    <div className={cn('flex flex-col gap-2', compact && 'text-xs')}>
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-text-secondary">
        <span className="inline-flex items-center gap-1.5">
          <TargetIcon className="h-3.5 w-3.5 text-text-muted" aria-hidden="true" />
          Target: <span className="font-mono text-text-primary">{recommendation.targetEntity.label}</span>
        </span>
      </div>

      {recommendation.expectedOutcomes.length > 0 && (
        <ul className="flex flex-wrap gap-1.5">
          {recommendation.expectedOutcomes.map((outcome) => (
            <li key={outcome} className="rounded-full bg-surface-sunken px-2 py-0.5 text-xs text-text-secondary">
              {outcome}
            </li>
          ))}
        </ul>
      )}

      <details className="group">
        <summary className="cursor-pointer select-none text-xs text-text-muted hover:text-text-secondary">
          Why this recommendation
        </summary>
        <div className="mt-1.5 flex flex-col gap-1 border-l-2 border-border pl-3">
          <p className="text-xs text-text-secondary">{recommendation.rationale}</p>
          <p className="font-mono text-[11px] text-text-muted">{recommendation.sourceRuleIds.join(', ')}</p>
        </div>
      </details>
    </div>
  )
}
