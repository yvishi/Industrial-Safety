import { cn } from '@/utils/cn'
import type { RiskLevel } from '@/features/plant/types/risk'
import type { Incident } from '../types/incident'

/** Mirrors RISK_LEVEL_BORDER_CLASS's color language (plant/utils/riskDisplay.ts) as a left
 * accent instead of a top one — this block is a callout, not a card header. */
const NARRATIVE_ACCENT_CLASS: Record<RiskLevel, string> = {
  normal: 'border-l-success bg-success-subtle',
  low: 'border-l-info bg-info-subtle',
  moderate: 'border-l-warning bg-warning-subtle',
  high: 'border-l-warning bg-warning-subtle',
  critical: 'border-l-danger bg-danger-subtle',
}

const NEUTRAL_ACCENT_CLASS = 'border-l-border-strong bg-surface-sunken'

export interface IncidentNarrativeProps {
  incident: Incident
}

/**
 * The Correlation Engine's deterministic, auto-generated narrative — a plain-language account
 * of what happened, built from the same structured facts as the rest of the record (never
 * free-form AI text). Rendered as the lead content of the incident, not a buried field, because
 * it's the fastest way for an operator to understand a record at a glance.
 */
export function IncidentNarrative({ incident }: IncidentNarrativeProps) {
  const level = incident.peakRiskSeverity ?? incident.riskSeverityAtOpen
  const accentClass = level ? NARRATIVE_ACCENT_CLASS[level] : NEUTRAL_ACCENT_CLASS

  return (
    <div className={cn('flex flex-col gap-2 rounded-lg border-l-4 px-5 py-4', accentClass)}>
      <span className="text-xs font-semibold uppercase tracking-wider text-text-secondary">What happened</span>
      <p className="text-base leading-relaxed text-text-primary">{incident.summary}</p>
    </div>
  )
}
