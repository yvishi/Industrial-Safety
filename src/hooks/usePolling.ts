import { useEffect, useRef, useState } from 'react'

export interface UsePollingResult<T> {
  data: T | null
  error: Error | null
  /** True only until the first successful (or failed) fetch — background refetches don't flip this. */
  isLoading: boolean
}

/**
 * Polls an async fetcher on an interval, keeping the last good `data` visible during
 * background refetches instead of flashing a loading state every tick.
 *
 * A lightweight, purpose-built alternative to a data-fetching library: this app has one
 * polling endpoint today. If more screens need shared caching/mutations, that's the point to
 * introduce something like TanStack Query — not before.
 */
export function usePolling<T>(fetcher: () => Promise<T>, intervalMs: number): UsePollingResult<T> {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<Error | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const fetcherRef = useRef(fetcher)
  fetcherRef.current = fetcher

  useEffect(() => {
    let cancelled = false
    let timer: ReturnType<typeof setTimeout> | undefined

    async function run() {
      try {
        const result = await fetcherRef.current()
        if (!cancelled) {
          setData(result)
          setError(null)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err : new Error('Request failed'))
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false)
          timer = setTimeout(run, intervalMs)
        }
      }
    }

    run()

    return () => {
      cancelled = true
      if (timer) clearTimeout(timer)
    }
  }, [intervalMs])

  return { data, error, isLoading }
}
