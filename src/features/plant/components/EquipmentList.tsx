import { StatusPill } from '@/components/ui/StatusPill'
import type { Equipment } from '../types/equipment'
import { equipmentStatusPill, formatStatusLabel } from '../utils/statusMapping'

export interface EquipmentListProps {
  equipment: Equipment[]
}

export function EquipmentList({ equipment }: EquipmentListProps) {
  if (equipment.length === 0) {
    return <p className="text-sm text-text-muted">No equipment registered in this zone.</p>
  }

  return (
    <ul className="flex flex-col divide-y divide-border rounded-lg border border-border">
      {equipment.map((item) => (
        <li key={item.id} className="flex flex-wrap items-center justify-between gap-x-3 gap-y-2 px-4 py-3">
          <div className="flex min-w-0 flex-1 flex-col">
            <span className="truncate text-sm font-medium text-text-primary">{item.name}</span>
            <span className="font-mono text-xs text-text-muted">{item.tagNumber}</span>
          </div>
          <StatusPill
            status={equipmentStatusPill(item.status)}
            label={formatStatusLabel(item.status)}
            className="shrink-0"
          />
        </li>
      ))}
    </ul>
  )
}
