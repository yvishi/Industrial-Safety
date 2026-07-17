import { useEffect, useRef, useState } from 'react'

export interface UseReportFetchResult<T> {
  data: T | null
  error: Error | null
  isLoading: boolean
}

/**
 * Fetches historical/on-demand report data once per dependency change — unlike the live-state
 * `usePolling` hook, report pages don't need to keep re-hitting the backend on an interval; they
 * just need to refetch when the filter (date range, zone) changes.
 */
export function useReportFetch<T>(fetcher: () => Promise<T>, deps: unknown[]): UseReportFetchResult<T> {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<Error | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const fetcherRef = useRef(fetcher)
  fetcherRef.current = fetcher

  useEffect(() => {
    let cancelled = false
    setIsLoading(true)

    fetcherRef
      .current()
      .then((result) => {
        if (!cancelled) {
          setData(result)
          setError(null)
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err : new Error('Request failed'))
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })

    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  return { data, error, isLoading }
}
