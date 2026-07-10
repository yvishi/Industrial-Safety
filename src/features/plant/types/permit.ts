export type PermitType =
  | 'hot_work'
  | 'confined_space'
  | 'line_breaking'
  | 'lockout_tagout'
  | 'working_at_height'
  | 'excavation'
  | 'electrical'

export type PermitStatus =
  | 'draft'
  | 'pending_approval'
  | 'approved'
  | 'active'
  | 'closed'
  | 'expired'
  | 'revoked'

export interface Permit {
  id: string
  zoneId: string
  permitNumber: string
  permitType: PermitType
  /** Isolation standard demanded before the work may start (lockout_tagout, blind_purge_and_gas_test, ...). */
  requiredIsolation: string | null
  status: PermitStatus
  description: string | null
  validFrom: string | null
  validUntil: string | null
}
