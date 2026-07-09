import { Loader2 } from 'lucide-react'
import { cn } from '@/utils/cn'

export interface SpinnerProps {
  className?: string
  size?: number
}

export function Spinner({ className, size = 16 }: SpinnerProps) {
  return (
    <Loader2
      className={cn('animate-spin text-text-muted', className)}
      style={{ width: size, height: size }}
      aria-label="Loading"
    />
  )
}
