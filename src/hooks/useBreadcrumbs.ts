import { useMatches } from 'react-router-dom'
import type { RouteHandle } from '@/types/navigation'
import { useBreadcrumbOverrides } from './useBreadcrumbLabel'

export interface Breadcrumb {
  label: string
  pathname: string
}

function hasCrumb(handle: unknown): handle is RouteHandle {
  return typeof (handle as RouteHandle | undefined)?.crumb === 'function'
}

/** Derives the breadcrumb trail for the current route from each matched route's `handle.crumb`,
 *  preferring a page-registered override (see useBreadcrumbLabel) for async-loaded titles. */
export function useBreadcrumbs(): Breadcrumb[] {
  const matches = useMatches()
  const overrides = useBreadcrumbOverrides()

  return matches
    .filter((match) => hasCrumb(match.handle))
    .map((match) => ({
      label: overrides.get(match.pathname) ?? (match.handle as RouteHandle).crumb(match.params),
      pathname: match.pathname,
    }))
}
