import type { HTMLAttributes, ReactNode } from 'react'
import { cn } from '@/utils/cn'

export interface SectionProps extends HTMLAttributes<HTMLElement> {
  title?: string
  description?: string
  actions?: ReactNode
}

/** Consistent content grouping used across pages — a titled block with optional actions. */
export function Section({ title, description, actions, className, children, ...props }: SectionProps) {
  return (
    <section className={cn('flex flex-col gap-4', className)} {...props}>
      {(title || description || actions) && (
        <div className="flex items-start justify-between gap-4">
          <div className="flex flex-col gap-1">
            {title && <h2 className="text-base font-semibold text-text-primary">{title}</h2>}
            {description && <p className="text-sm text-text-secondary">{description}</p>}
          </div>
          {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
        </div>
      )}
      {children}
    </section>
  )
}
