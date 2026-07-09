import { useEffect, useState } from 'react'

export interface LiveIndicatorProps {
  generatedAt: string
}

function formatAge(seconds: number): string {
  if (seconds < 2) return 'just now'
  if (seconds < 60) return `${Math.floor(seconds)}s ago`
  return `${Math.floor(seconds / 60)}m ago`
}

/** Ticks locally so "updated Xs ago" stays honest between polls, not just when new data arrives. */
export function LiveIndicator({ generatedAt }: LiveIndicatorProps) {
  const [, forceTick] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => forceTick((n) => n + 1), 1000)
    return () => clearInterval(interval)
  }, [])

  const ageSeconds = (Date.now() - new Date(generatedAt).getTime()) / 1000

  return (
    <div className="flex items-center gap-1.5 text-xs text-text-muted">
      <span className="h-1.5 w-1.5 rounded-full bg-success" aria-hidden="true" />
      <span>Live · updated {formatAge(ageSeconds)}</span>
    </div>
  )
}
