export type PermitType =
  | 'hot_work'
  | 'confined_space'
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
  status: PermitStatus
  description: string | null
  validFrom: string | null
  validUntil: string | null
}
