import type { LucideIcon } from 'lucide-react'

export interface CapabilityPlaceholderProps {
  icon: LucideIcon
  title: string
  description: string
}

/** A roadmap tile for a future module that will attach to a zone (sensors, incidents, AI, ...). */
export function CapabilityPlaceholder({ icon: Icon, title, description }: CapabilityPlaceholderProps) {
  return (
    <div className="flex flex-col gap-2 rounded-lg border border-dashed border-border p-4">
      <div className="flex h-8 w-8 items-center justify-center rounded-md bg-surface-sunken text-text-muted">
        <Icon className="h-4 w-4" aria-hidden="true" />
      </div>
      <p className="text-sm font-medium text-text-primary">{title}</p>
      <p className="text-xs text-text-secondary">{description}</p>
    </div>
  )
}
