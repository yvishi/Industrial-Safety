import { cva } from 'class-variance-authority'
import { formatRelativeTime } from '@/features/plant/utils/time'
import { cn } from '@/utils/cn'
import type { SafetyVerdict } from '../utils/safetyVerdict'

export interface SafetyStatusBandProps {
  verdict: SafetyVerdict
}

const bandVariants = cva('rounded-lg border p-6 sm:p-8 border-l-4', {
  variants: {
    tier: {
      safe: 'border-success/30 bg-success-subtle border-l-success',
      attention: 'border-warning/30 bg-warning-subtle border-l-warning',
      emergency: 'border-danger/30 bg-danger-subtle border-l-danger',
    },
  },
})

const dotVariants = cva('h-3 w-3 shrink-0 rounded-full', {
  variants: {
    tier: {
      safe: 'bg-success',
      attention: 'bg-warning',
      emergency: 'bg-danger animate-pulse motion-reduce:animate-none',
    },
  },
})

const headlineVariants = cva('text-2xl sm:text-3xl font-bold tracking-tight', {
  variants: {
    tier: {
      safe: 'text-success',
      attention: 'text-warning',
      emergency: 'text-danger',
    },
  },
})

export function SafetyStatusBand({ verdict }: SafetyStatusBandProps) {
  const { tier, headline, reason, evaluatedAt } = verdict

  return (
    <div role="status" aria-live="polite" className={cn(bandVariants({ tier }))}>
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-3">
          <span className={cn(dotVariants({ tier }))} aria-hidden="true" />
          <span className={cn(headlineVariants({ tier }))}>{headline}</span>
        </div>
        <p className="text-sm sm:text-base text-text-secondary">{reason}</p>
        <p className="text-xs text-text-muted">Last evaluated {formatRelativeTime(evaluatedAt)}</p>
      </div>
    </div>
  )
}
