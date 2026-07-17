import { Link } from 'react-router-dom'
import { ArrowRight, ChevronRight, CircleCheck } from 'lucide-react'
import { ROUTES, buildIncidentPath } from '@/app/routes'
import { Section } from '@/components/ui/Section'
import { EmptyState } from '@/components/ui/EmptyState'
import { StatusPill } from '@/components/ui/StatusPill'
import { Badge } from '@/components/ui/Badge'
import { RISK_LEVEL_LABEL, riskLevelStatus } from '@/features/plant/utils/riskDisplay'
import { incidentClassificationLabel } from '@/features/incidents/utils/incidentDisplay'
import { formatRelativeTime } from '@/features/incidents/utils/time'
import type { Incident } from '@/features/incidents/types/incident'

export interface IncidentsAttentionListProps {
  /** Already sorted most-urgent-first and already sliced to the number of rows to display
   * (e.g. top 5) — do not re-sort or re-slice here. */
  incidents: Incident[]
  /** Total count of ALL open incidents (which may be larger than incidents.length) — used only
   * for the empty-state copy, not for a badge/counter on the list itself. */
  totalOpenCount: number
}

function emptyStateDescription(totalOpenCount: number): string {
  if (totalOpenCount === 0) return 'No open incidents.'
  return `${totalOpenCount} open incident${totalOpenCount === 1 ? '' : 's'} being tracked, none urgent right now.`
}

/**
 * Answers "which incidents need immediate attention" — a short, pre-ranked list of open
 * incidents. Deliberately quiet: the top safety banner elsewhere on the dashboard is the one
 * loud element, this is a scan-and-click list.
 */
export function IncidentsAttentionList({ incidents, totalOpenCount }: IncidentsAttentionListProps) {
  return (
    <Section
      title="Incidents Needing Attention"
      description="Open incidents ranked by urgency — reportable classification or high/critical severity first."
      actions={
        <Link to={ROUTES.incidents} className="flex items-center gap-1 text-sm text-accent hover:underline">
          View all
          <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
        </Link>
      }
    >
      {incidents.length === 0 ? (
        <EmptyState
          icon={CircleCheck}
          title="Nothing needs attention"
          description={emptyStateDescription(totalOpenCount)}
        />
      ) : (
        <div className="flex flex-col gap-2">
          {incidents.map((incident) => (
            <Link
              key={incident.id}
              to={buildIncidentPath(incident.id)}
              className="flex items-center gap-3 rounded-lg border border-border p-3.5 hover:bg-surface-hover transition-colors"
            >
              <StatusPill
                status={riskLevelStatus(incident.peakRiskSeverity ?? 'normal')}
                label={RISK_LEVEL_LABEL[incident.peakRiskSeverity ?? 'normal']}
              />
              <div className="flex min-w-0 flex-col gap-0.5">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-text-primary line-clamp-1">{incident.title}</span>
                  {incident.classification === 'reportable_incident' && (
                    <Badge variant="danger">{incidentClassificationLabel(incident.classification)}</Badge>
                  )}
                </div>
                <span className="text-xs text-text-muted">
                  {incident.zoneName} · {formatRelativeTime(incident.openedAt)}
                </span>
              </div>
              <ChevronRight className="ml-auto h-4 w-4 shrink-0 text-text-muted" aria-hidden="true" />
            </Link>
          ))}
        </div>
      )}
    </Section>
  )
}
