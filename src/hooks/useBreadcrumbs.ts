import { useMatches } from 'react-router-dom'
import type { RouteHandle } from '@/types/navigation'

export interface Breadcrumb {
  label: string
  pathname: string
}

function hasCrumb(handle: unknown): handle is RouteHandle {
  return typeof (handle as RouteHandle | undefined)?.crumb === 'function'
}

/** Derives the breadcrumb trail for the current route from each matched route's `handle.crumb`. */
export function useBreadcrumbs(): Breadcrumb[] {
  const matches = useMatches()

  return matches
    .filter((match) => hasCrumb(match.handle))
    .map((match) => ({
      label: (match.handle as RouteHandle).crumb(match.params),
      pathname: match.pathname,
    }))
}
