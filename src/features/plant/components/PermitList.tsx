import { StatusPill } from '@/components/ui/StatusPill'
import type { Permit } from '../types/permit'
import { formatStatusLabel, permitStatusPill } from '../utils/statusMapping'

export interface PermitListProps {
  permits: Permit[]
}

export function PermitList({ permits }: PermitListProps) {
  if (permits.length === 0) {
    return <p className="text-sm text-text-muted">No active permits for this zone.</p>
  }

  return (
    <ul className="flex flex-col divide-y divide-border rounded-lg border border-border">
      {permits.map((permit) => (
        <li key={permit.id} className="flex flex-wrap items-center justify-between gap-x-3 gap-y-2 px-4 py-3">
          <div className="flex min-w-0 flex-1 flex-col">
            <span className="truncate text-sm font-medium text-text-primary">
              {permit.description ?? formatStatusLabel(permit.permitType)}
            </span>
            <span className="truncate font-mono text-xs text-text-muted">
              {permit.permitNumber} · {formatStatusLabel(permit.permitType)}
              {permit.requiredIsolation && permit.requiredIsolation !== 'none'
                ? ` · ${formatStatusLabel(permit.requiredIsolation)}`
                : ''}
            </span>
          </div>
          <StatusPill
            status={permitStatusPill(permit.status)}
            label={formatStatusLabel(permit.status)}
            className="shrink-0"
          />
        </li>
      ))}
    </ul>
  )
}
