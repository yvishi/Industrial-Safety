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
