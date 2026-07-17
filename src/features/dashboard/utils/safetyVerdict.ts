import type { PlantRiskSummary } from '@/features/plant/types/risk'
import type { Incident } from '@/features/incidents/types/incident'

export type SafetyTier = 'safe' | 'attention' | 'emergency'

export interface SafetyVerdict {
  tier: SafetyTier
  headline: string
  reason: string
  evaluatedAt: string
}

const RISK_RANK: Record<string, number> = { normal: 0, low: 1, moderate: 2, high: 3, critical: 4 }

const TIER_HEADLINE: Record<SafetyTier, string> = {
  safe: 'Safe',
  attention: 'Attention Needed',
  emergency: 'Emergency',
}

/** "Needs immediate attention" = reportable by classification, or peaked at high/critical risk
 * severity — same RISK_RANK convention IncidentsListPage's pickTopIncident already uses, so
 * "urgent" means the same thing everywhere in the app. */
export function isUrgentIncident(incident: Incident): boolean {
  if (incident.classification === 'reportable_incident') return true
  const rank = RISK_RANK[incident.peakRiskSeverity ?? 'normal'] ?? 0
  return rank >= RISK_RANK.high
}

function rankIncidentUrgency(incident: Incident): number {
  const rank = RISK_RANK[incident.peakRiskSeverity ?? 'normal'] ?? 0
  return incident.classification === 'reportable_incident' ? rank + 1 : rank
}

/** Most urgent first; oldest-first among ties, so a long-open incident surfaces before a
 * same-severity one that just opened. */
export function sortByUrgency(incidents: Incident[]): Incident[] {
  return [...incidents].sort((a, b) => {
    const diff = rankIncidentUrgency(b) - rankIncidentUrgency(a)
    if (diff !== 0) return diff
    return new Date(a.openedAt).getTime() - new Date(b.openedAt).getTime()
  })
}

/**
 * The single glanceable verdict at the top of the dashboard. "Is the refinery safe" has to
 * collapse every signal (ESD state, per-zone risk, open incident severity) into one of three
 * tiers, worst-signal-wins — there must never be a case where the band reads calm while
 * something underneath it isn't.
 */
export function computeSafetyVerdict(
  riskSummary: PlantRiskSummary,
  openIncidents: Incident[],
): SafetyVerdict {
  const evaluatedAt = riskSummary.generatedAt
  const urgentIncidents = openIncidents.filter(isUrgentIncident)
  const highestZone = riskSummary.zones.find((z) => z.zoneId === riskSummary.highestRiskZoneId)

  if (riskSummary.plantWideEmergencyActive) {
    return {
      tier: 'emergency',
      headline: TIER_HEADLINE.emergency,
      reason: highestZone
        ? `Emergency shutdown active — ${highestZone.zoneName} triggered the plant-wide ESD.`
        : 'Emergency shutdown active on the plant.',
      evaluatedAt,
    }
  }

  const criticalZones = riskSummary.zones.filter((z) => z.level === 'critical')
  if (criticalZones.length > 0) {
    const zone = criticalZones[0]
    return {
      tier: 'emergency',
      headline: TIER_HEADLINE.emergency,
      reason:
        criticalZones.length === 1
          ? `${zone.zoneName} is at critical risk (score ${zone.score}).`
          : `${criticalZones.length} zones are at critical risk, including ${zone.zoneName}.`,
      evaluatedAt,
    }
  }

  if (urgentIncidents.length > 0) {
    const topIncident = sortByUrgency(urgentIncidents)[0]
    return {
      tier: 'attention',
      headline: TIER_HEADLINE.attention,
      reason:
        urgentIncidents.length === 1
          ? `1 incident needs immediate attention — "${topIncident.title}" in ${topIncident.zoneName}.`
          : `${urgentIncidents.length} incidents need immediate attention, including "${topIncident.title}".`,
      evaluatedAt,
    }
  }

  const highZones = riskSummary.zones.filter((z) => z.level === 'high')
  if (highZones.length > 0) {
    const zone = highZones[0]
    return {
      tier: 'attention',
      headline: TIER_HEADLINE.attention,
      reason:
        highZones.length === 1
          ? `${zone.zoneName} is at high risk (score ${zone.score}).`
          : `${highZones.length} zones are at high risk, including ${zone.zoneName}.`,
      evaluatedAt,
    }
  }

  return {
    tier: 'safe',
    headline: TIER_HEADLINE.safe,
    reason: `All ${riskSummary.zones.length} zones within normal operating parameters.${
      openIncidents.length > 0
        ? ` ${openIncidents.length} open incident${openIncidents.length === 1 ? '' : 's'} being tracked, none urgent.`
        : ' No open incidents.'
    }`,
    evaluatedAt,
  }
}
