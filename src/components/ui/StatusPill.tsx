import { cva } from 'class-variance-authority'
import { cn } from '@/utils/cn'
import type { Status } from '@/types/common'

const pillVariants = cva('inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium', {
  variants: {
    status: {
      operational: 'border-success/20 bg-success-subtle text-success',
      warning: 'border-warning/20 bg-warning-subtle text-warning',
      critical: 'border-danger/20 bg-danger-subtle text-danger',
      offline: 'border-border bg-surface-sunken text-text-muted',
      info: 'border-info/20 bg-info-subtle text-info',
    } satisfies Record<Status, string>,
  },
})

const dotVariants = cva('h-1.5 w-1.5 rounded-full', {
  variants: {
    status: {
      operational: 'bg-success',
      warning: 'bg-warning',
      critical: 'bg-danger',
      offline: 'bg-text-muted',
      info: 'bg-info',
    } satisfies Record<Status, string>,
  },
})

const STATUS_LABEL: Record<Status, string> = {
  operational: 'Operational',
  warning: 'Warning',
  critical: 'Critical',
  offline: 'Offline',
  info: 'Info',
}

export interface StatusPillProps {
  status: Status
  label?: string
  className?: string
}

export function StatusPill({ status, label, className }: StatusPillProps) {
  return (
    <span className={cn(pillVariants({ status }), className)}>
      <span className={cn(dotVariants({ status }))} aria-hidden="true" />
      {label ?? STATUS_LABEL[status]}
    </span>
  )
}
