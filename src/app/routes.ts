/** Central path constants — import these instead of hardcoding route strings. */
export const ROUTES = {
  dashboard: '/',
  plant: '/plant',
  incidents: '/incidents',
  timeline: '/timeline',
  reports: '/reports',
  settings: '/settings',
} as const

export function buildZonePath(zoneId: string): string {
  return `${ROUTES.plant}/zones/${zoneId}`
}

export function buildIncidentPath(incidentId: string): string {
  return `${ROUTES.incidents}/${incidentId}`
}
