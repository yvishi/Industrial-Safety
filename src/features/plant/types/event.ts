export type EventSeverity = 'info' | 'notice' | 'warning' | 'critical'

export interface PlantEvent {
  id: string
  eventType: string
  title: string
  description: string | null
  occurredAt: string
  zoneId: string | null
  riskSnapshotId: string | null
  incidentId: string | null
  actorType: 'system' | 'operator'
  actorId: string | null
  severity: EventSeverity
}
