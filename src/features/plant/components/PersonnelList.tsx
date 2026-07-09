import { User } from 'lucide-react'
import type { Worker } from '../types/worker'
import { formatStatusLabel } from '../utils/statusMapping'

export interface PersonnelListProps {
  workers: Worker[]
}

export function PersonnelList({ workers }: PersonnelListProps) {
  if (workers.length === 0) {
    return <p className="text-sm text-text-muted">No one currently in this zone.</p>
  }

  return (
    <ul className="flex flex-col divide-y divide-border rounded-lg border border-border">
      {workers.map((worker) => (
        <li key={worker.id} className="flex items-center gap-3 px-4 py-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-surface-sunken text-text-secondary">
            <User className="h-4 w-4" aria-hidden="true" />
          </div>
          <div className="flex min-w-0 flex-col">
            <span className="truncate text-sm font-medium text-text-primary">
              {worker.firstName} {worker.lastName}
            </span>
            <span className="truncate text-xs text-text-muted">
              {formatStatusLabel(worker.role)}
              {worker.shift ? ` · ${formatStatusLabel(worker.shift)} shift` : ''}
            </span>
          </div>
        </li>
      ))}
    </ul>
  )
}
