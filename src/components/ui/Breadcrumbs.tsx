import { Fragment } from 'react'
import { Link } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'
import type { Breadcrumb } from '@/hooks/useBreadcrumbs'

export interface BreadcrumbsProps {
  items: Breadcrumb[]
}

export function Breadcrumbs({ items }: BreadcrumbsProps) {
  if (items.length === 0) return null

  return (
    <nav aria-label="Breadcrumb" className="flex min-w-0 items-center gap-1.5 text-sm">
      {items.map((item, index) => {
        const isLast = index === items.length - 1
        return (
          <Fragment key={item.pathname}>
            {index > 0 && (
              <ChevronRight className="h-3.5 w-3.5 shrink-0 text-text-muted" aria-hidden="true" />
            )}
            {isLast ? (
              <span className="truncate font-semibold text-text-primary">{item.label}</span>
            ) : (
              <Link
                to={item.pathname}
                className="shrink-0 text-text-secondary transition-colors hover:text-text-primary"
              >
                {item.label}
              </Link>
            )}
          </Fragment>
        )
      })}
    </nav>
  )
}
