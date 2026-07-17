import type { ReactNode } from 'react'

/** Shared by components that accept a Tailwind `className` override. */
export interface WithClassName {
  className?: string
}

/** Shared by components composed purely from children. */
export interface WithChildren {
  children?: ReactNode
}

export type Status = 'operational' | 'warning' | 'critical' | 'offline' | 'info'

/** Generic paginated response shape — camelCase counterpart of each feature's own
 * RawPage<T> wire type (see e.g. src/features/plant/services/wireTypes.ts). */
export interface Page<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}
