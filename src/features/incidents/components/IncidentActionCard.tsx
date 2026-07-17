import { Link } from 'react-router-dom'
import { AlertTriangle } from 'lucide-react'
import { buildIncidentPath } from '@/app/routes'
import { buttonVariants } from '@/components/ui/Button'
import type { Incident } from '../types/incident'
import { incidentClassificationLabel } from '../utils/incidentDisplay'

export interface IncidentActionCardProps {
  incident: Incident
}

/** The single most urgent open incident, presented the same way the plant-wide Action Queue
 * presents its own top recommendation — the same visual command, extended to incidents so the
 * two pages read as one continuous language. */
export function IncidentActionCard({ incident }: IncidentActionCardProps) {
  return (
    <div className="flex flex-col gap-4 rounded-lg border border-danger/30 bg-danger-subtle p-5">
      <div className="flex items-center gap-2 text-danger">
        <AlertTriangle className="h-4 w-4" aria-hidden="true" />
        <span className="text-xs font-semibold uppercase tracking-wider">Action Required</span>
        <span className="ml-auto text-xs font-medium text-text-secondary">{incident.zoneName}</span>
      </div>

      <div className="flex flex-col gap-1.5">
        <h3 className="text-lg font-semibold text-text-primary">{incident.title}</h3>
        <p className="text-sm text-text-secondary">{incident.summary}</p>
      </div>

      <div className="flex items-center gap-2 pt-1">
        <Link to={buildIncidentPath(incident.id)} className={buttonVariants({ variant: 'destructive', size: 'sm' })}>
          View incident
        </Link>
        <span className="ml-auto text-xs text-text-muted">{incidentClassificationLabel(incident.classification)}</span>
      </div>
    </div>
  )
}
