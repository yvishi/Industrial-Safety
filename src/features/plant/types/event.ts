export interface PlantEvent {
  id: string
  eventType: string
  title: string
  description: string | null
  occurredAt: string
  zoneId: string | null
}
