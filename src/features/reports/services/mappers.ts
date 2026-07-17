import type { RiskCategoryKey, TrendDirection } from '@/features/plant/types/risk'
import type { IncidentClassification } from '@/features/incidents/types/incident'
import type {
  IncidentResponseReport,
  PeriodGranularity,
  SafetyTrendReport,
  ZoneHazardReport,
} from '../types/reports'
import type {
  RawIncidentResponseReport,
  RawSafetyTrendReport,
  RawZoneHazardReport,
} from './wireTypes'

export function mapSafetyTrendReport(raw: RawSafetyTrendReport): SafetyTrendReport {
  return {
    since: raw.since,
    until: raw.until,
    zoneId: raw.zone_id,
    periodGranularity: raw.period_granularity as PeriodGranularity,
    periods: raw.periods.map((period) => ({
      periodStart: period.period_start,
      incidentsOpened: period.incidents_opened,
      incidentsResolved: period.incidents_resolved,
      normalCount: period.normal_count,
      lowCount: period.low_count,
      moderateCount: period.moderate_count,
      highCount: period.high_count,
      criticalCount: period.critical_count,
    })),
    totalIncidentsOpened: raw.total_incidents_opened,
    totalIncidentsResolved: raw.total_incidents_resolved,
    trendDirection: raw.trend_direction as TrendDirection,
    trendSummary: raw.trend_summary,
  }
}

export function mapZoneHazardReport(raw: RawZoneHazardReport): ZoneHazardReport {
  return {
    since: raw.since,
    until: raw.until,
    zones: raw.zones.map((zone) => ({
      zoneId: zone.zone_id,
      zoneName: zone.zone_name,
      incidentCount: zone.incident_count,
      openIncidentCount: zone.open_incident_count,
      reportableIncidentCount: zone.reportable_incident_count,
      avgRiskScore: zone.avg_risk_score,
      topCategory: zone.top_category as RiskCategoryKey | null,
    })),
    hazardCategories: raw.hazard_categories.map((entry) => ({
      category: entry.category as RiskCategoryKey,
      triggerCount: entry.trigger_count,
    })),
    topRules: raw.top_rules.map((rule) => ({
      ruleId: rule.rule_id,
      category: rule.category as RiskCategoryKey,
      description: rule.description,
      triggerCount: rule.trigger_count,
    })),
  }
}

export function mapIncidentResponseReport(raw: RawIncidentResponseReport): IncidentResponseReport {
  return {
    since: raw.since,
    until: raw.until,
    zoneId: raw.zone_id,
    incidentsResolvedCount: raw.incidents_resolved_count,
    incidentsClosedCount: raw.incidents_closed_count,
    meanTimeToResolveHours: raw.mean_time_to_resolve_hours,
    meanTimeToCloseHours: raw.mean_time_to_close_hours,
    recommendationsAcknowledgedCount: raw.recommendations_acknowledged_count,
    meanTimeToAcknowledgeMinutes: raw.mean_time_to_acknowledge_minutes,
    classificationBreakdown: raw.classification_breakdown.map((entry) => ({
      classification: entry.classification as IncidentClassification,
      count: entry.count,
    })),
    topRecommendationTemplates: raw.top_recommendation_templates.map((template) => ({
      templateId: template.template_id,
      title: template.title,
      category: template.category as RiskCategoryKey,
      triggerCount: template.trigger_count,
    })),
  }
}
