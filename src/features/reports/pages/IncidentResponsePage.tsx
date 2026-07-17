import { useEffect, useState } from 'react'
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { BellRing, CheckCircle2, Timer, WifiOff } from 'lucide-react'
import { PageHeader } from '@/components/ui/PageHeader'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Skeleton } from '@/components/ui/Skeleton'
import { EmptyState } from '@/components/ui/EmptyState'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/Table'
import { fetchPlantState } from '@/features/plant/services/plantService'
import type { Zone } from '@/features/plant'
import type { IncidentClassification } from '@/features/incidents/types/incident'
import { incidentClassificationLabel } from '@/features/incidents/utils/incidentDisplay'
import { useAnalyticsRange } from '../context/AnalyticsRangeContext'
import { ReportKpiTile } from '../components/ReportKpiTile'
import { useReportFetch } from '../hooks/useReportFetch'
import { fetchIncidentResponse } from '../services/reportService'
import { RISK_CATEGORY_LABEL, formatHours, formatMinutes } from '../utils/reportDisplay'

/** Fixed left-to-right severity order, independent of whatever order the backend returns. */
const CLASSIFICATION_ORDER: IncidentClassification[] = [
  'operational_episode',
  'near_miss',
  'safety_incident',
  'reportable_incident',
]

const CLASSIFICATION_COLOR: Record<IncidentClassification, string> = {
  operational_episode: 'var(--color-info)',
  near_miss: 'var(--color-warning)',
  safety_incident: 'var(--color-warning)',
  reportable_incident: 'var(--color-danger)',
}

/** Operational performance analysis — "how fast do we resolve incidents / act on
 * recommendations?" Uses the analytics range shared across every Safety Analytics page. */
export function IncidentResponsePage() {
  const { range } = useAnalyticsRange()
  const [zones, setZones] = useState<Zone[]>([])
  const [zoneId, setZoneId] = useState<string>('')

  useEffect(() => {
    fetchPlantState().then((state) => setZones(state.zones.map((entry) => entry.zone)))
  }, [])

  const { data, error, isLoading } = useReportFetch(
    () => fetchIncidentResponse({ since: range.since, until: range.until, zoneId: zoneId || undefined }),
    [range.since, range.until, zoneId],
  )

  const chartData = data
    ? CLASSIFICATION_ORDER.map((classification) => ({
        classification,
        label: incidentClassificationLabel(classification),
        count: data.classificationBreakdown.find((entry) => entry.classification === classification)?.count ?? 0,
      }))
    : []

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Incident Response"
        description="Operational performance analysis — how fast incidents get resolved and recommendations get acted on."
        actions={
          <div className="flex items-center gap-2">
            <label htmlFor="response-zone" className="text-sm font-medium text-text-primary">
              Zone
            </label>
            <select
              id="response-zone"
              value={zoneId}
              onChange={(event) => setZoneId(event.target.value)}
              className="h-9 rounded-md border border-border bg-surface px-3 text-sm text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            >
              <option value="">All zones</option>
              {zones.map((zone) => (
                <option key={zone.id} value={zone.id}>
                  {zone.name}
                </option>
              ))}
            </select>
          </div>
        }
      />

      {isLoading ? (
        <div className="flex flex-col gap-4">
          <div className="grid gap-4 sm:grid-cols-3">
            <Skeleton className="h-24" />
            <Skeleton className="h-24" />
            <Skeleton className="h-24" />
          </div>
          <Skeleton className="h-72" />
          <Skeleton className="h-56" />
        </div>
      ) : error || !data ? (
        <EmptyState
          icon={WifiOff}
          title="Can't reach the reporting service"
          description="The backend isn't responding. Make sure it's running, then try again."
        />
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-3">
            <ReportKpiTile
              label="Mean Time to Resolve"
              value={formatHours(data.meanTimeToResolveHours)}
              sublabel={`${data.incidentsResolvedCount} resolved`}
              icon={Timer}
            />
            <ReportKpiTile
              label="Mean Time to Close"
              value={formatHours(data.meanTimeToCloseHours)}
              sublabel={`${data.incidentsClosedCount} closed`}
              icon={CheckCircle2}
            />
            <ReportKpiTile
              label="Mean Time to Acknowledge"
              value={formatMinutes(data.meanTimeToAcknowledgeMinutes)}
              sublabel={`${data.recommendationsAcknowledgedCount} acknowledged`}
              icon={BellRing}
            />
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Incidents by Classification</CardTitle>
            </CardHeader>
            <CardContent className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <CartesianGrid vertical={false} stroke="var(--color-border)" />
                  <XAxis dataKey="label" stroke="var(--color-text-muted)" fontSize={12} tickLine={false} />
                  <YAxis stroke="var(--color-text-muted)" fontSize={12} tickLine={false} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{
                      background: 'var(--color-surface)',
                      border: '1px solid var(--color-border)',
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                  />
                  <Bar dataKey="count" name="Incidents" radius={[4, 4, 0, 0]} maxBarSize={48}>
                    {chartData.map((entry) => (
                      <Cell key={entry.classification} fill={CLASSIFICATION_COLOR[entry.classification]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Top Recommendation Templates</CardTitle>
            </CardHeader>
            <CardContent>
              {data.topRecommendationTemplates.length === 0 ? (
                <p className="text-sm text-text-secondary">No recommendations triggered across the selected period.</p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Recommendation</TableHead>
                      <TableHead>Category</TableHead>
                      <TableHead>Triggers</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.topRecommendationTemplates.map((template) => (
                      <TableRow key={template.templateId}>
                        <TableCell>{template.title}</TableCell>
                        <TableCell className="text-text-secondary">{RISK_CATEGORY_LABEL[template.category]}</TableCell>
                        <TableCell>{template.triggerCount}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}
