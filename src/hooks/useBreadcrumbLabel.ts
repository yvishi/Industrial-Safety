import { useEffect, useSyncExternalStore } from 'react'

/**
 * Lets a page override its own breadcrumb segment once an async-loaded title becomes known
 * (e.g. a zone name that only exists after the plant state has been fetched). Route `handle.crumb`
 * functions are synchronous, so they can't express this — this is the escape hatch.
 */

type Listener = () => void

let snapshot: ReadonlyMap<string, string> = new Map()
const listeners = new Set<Listener>()

function notify() {
  listeners.forEach((listener) => listener())
}

function subscribe(listener: Listener) {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

function getSnapshot() {
  return snapshot
}

function setOverride(pathname: string, label: string) {
  if (snapshot.get(pathname) === label) return
  const next = new Map(snapshot)
  next.set(pathname, label)
  snapshot = next
  notify()
}

function clearOverride(pathname: string) {
  if (!snapshot.has(pathname)) return
  const next = new Map(snapshot)
  next.delete(pathname)
  snapshot = next
  notify()
}

export function useBreadcrumbLabel(pathname: string, label: string | undefined) {
  useEffect(() => {
    if (!label) return
    setOverride(pathname, label)
    return () => clearOverride(pathname)
  }, [pathname, label])
}

export function useBreadcrumbOverrides(): ReadonlyMap<string, string> {
  return useSyncExternalStore(subscribe, getSnapshot)
}
