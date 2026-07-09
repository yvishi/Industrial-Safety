import type { LucideIcon } from 'lucide-react'

export interface NavItem {
  label: string
  path: string
  icon: LucideIcon
}

/** Attached to router route objects via `handle` to drive breadcrumb generation. */
export interface RouteHandle {
  crumb: (params: Record<string, string | undefined>) => string
}
