/**
 * Raw shapes exactly as the backend's Pydantic schemas serialize them (snake_case).
 * Never imported outside this services/ folder — everything else in the app sees the
 * camelCase domain types from ../types, mapped below.
 */

export interface RawIncident {
  id: string
  created_at: string
  updated_at: string
  primary_zone_id: string
  zone_name: string
  affected_zone_ids: string[]
  status: string
  origin: string
  classification: string
  risk_severity_at_open: string | null
  peak_risk_severity: string | null
  incident_severity: string | null
  title: string
  summary: string
  opened_at: string
  resolved_at: string | null
  closed_at: string | null
  root_cause: string | null
  corrective_actions: string[]
  opened_by_id: string | null
  closed_by_id: string | null
}

export interface RawPage<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}
