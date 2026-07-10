import type { ReactNode } from 'react'

export interface MetricRowProps {
  label: string
  value: ReactNode
}

export function MetricRow({ label, value }: MetricRowProps) {
  return (
    <div className="flex items-center justify-between gap-3 py-2.5">
      <dt className="text-sm text-text-secondary">{label}</dt>
      <dd className="text-sm font-medium text-text-primary">{value}</dd>
    </div>
  )
}
