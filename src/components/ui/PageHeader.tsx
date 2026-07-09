import type { HTMLAttributes, ReactNode } from 'react'
import { cn } from '@/utils/cn'

export interface PageHeaderProps extends HTMLAttributes<HTMLElement> {
  title: string
  description?: string
  actions?: ReactNode
}

/** Standard title block placed at the top of every page. */
export function PageHeader({ title, description, actions, className, ...props }: PageHeaderProps) {
  return (
    <header
      className={cn('flex flex-col gap-4 border-b border-border pb-5 sm:flex-row sm:items-center sm:justify-between', className)}
      {...props}
    >
      <div className="flex flex-col gap-1">
        <h1 className="text-xl font-semibold tracking-tight text-text-primary">{title}</h1>
        {description && <p className="text-sm text-text-secondary">{description}</p>}
      </div>
      {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
    </header>
  )
}
