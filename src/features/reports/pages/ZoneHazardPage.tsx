import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { AlertTriangle, ArrowLeft, MapPinned, WifiOff } from 'lucide-react'
import { PageHeader } from '@/components/ui/PageHeader'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Skeleton } from '@/components/ui/Skeleton'
import { EmptyState } from '@/components/ui/EmptyState'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/Table'
import { ROUTES, buildZonePath } from '@/app/routes'
import { DateRangeFilter, computeRange, type DateRange } from '../components/DateRangeFilter'
import { useReportFetch } from '../hooks/useReportFetch'
import { fetchZoneHazardReport } from '../services/reportService'
import { RISK_CATEGORY_LABEL } from '../utils/reportDisplay'

const CHART_MARGIN = { top: 4, right: 24, bottom: 4, left: 4 }

/** "Which zones/hazards need attention?" — cross-zone hazard comparison. */
export function ZoneHazardPage() {
  const navigate = useNavigate()
  const [range, setRange] = useState<DateRange>(() => computeRange(30))

  const { data, error, isLoading } = useReportFetch(
    () => fetchZoneHazardReport({ since: range.since, until: range.until }),
    [range.since, range.until],
  )

  const topZones = data ? [...data.zones].sort((a, b) => b.incidentCount - a.incidentCount).slice(0, 10) : []

  return (
    <div className="flex flex-col gap-6">
      <Link
        to={ROUTES.reports}
        className="inline-flex w-fit items-center gap-1.5 text-sm text-text-secondary transition-colors hover:text-text-primary"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden="true" />
        Reports overview
      </Link>

      <PageHeader
        title="Zones & Hazards"
        description="Cross-zone comparison of incidents and hazard categories — which zones and hazards need attention?"
      />

      <DateRangeFilter onChange={setRange} />

      {isLoading ? (
        <div className="flex flex-col gap-4">
          <Skeleton className="h-80" />
          <Skeleton className="h-72" />
          <Skeleton className="h-56" />
        </div>
      ) : error || !data ? (
        <EmptyState
          icon={WifiOff}
          title="Can't reach the reporting service"
          description="The backend isn't responding. Make sure it's running, then try again."
        />
      ) : data.zones.length === 0 ? (
        <EmptyState
          icon={MapPinned}
          title="No incidents in this range"
          description="No zone had any incidents across the selected period."
        />
      ) : (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Zones by Incident Count</CardTitle>
              <div className="mt-1 flex items-center gap-4 text-xs text-text-secondary">
                <span className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-danger" aria-hidden="true" />
                  Has reportable incident
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-accent" aria-hidden="true" />
                  No reportable incidents
                </span>
              </div>
            </CardHeader>
            <CardContent className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={topZones} layout="vertical" margin={CHART_MARGIN}>
                  <CartesianGrid horizontal={false} stroke="var(--color-border)" />
                  <XAxis type="number" stroke="var(--color-text-muted)" fontSize={12} tickLine={false} allowDecimals={false} />
                  <YAxis
                    type="category"
                    dataKey="zoneName"
                    stroke="var(--color-text-muted)"
                    fontSize={12}
                    tickLine={false}
                    width={160}
                  />
                  <Tooltip
                    contentStyle={{
                      background: 'var(--color-surface)',
                      border: '1px solid var(--color-border)',
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                  />
                  <Bar
                    dataKey="incidentCount"
                    name="Incidents"
                    radius={[0, 4, 4, 0]}
                    maxBarSize={20}
                    cursor="pointer"
                    onClick={(entry) => navigate(buildZonePath((entry as { zoneId: string }).zoneId))}
                  >
                    {topZones.map((zone) => (
                      <Cell
                        key={zone.zoneId}
                        fill={zone.reportableIncidentCount > 0 ? 'var(--color-danger)' : 'var(--color-accent)'}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Hazard Categories by Trigger Count</CardTitle>
            </CardHeader>
            <CardContent className="h-72">
              {data.hazardCategories.length === 0 ? (
                <EmptyState
                  icon={AlertTriangle}
                  title="No hazards triggered"
                  description="No risk rules fired across the selected period."
                  className="h-full justify-center border-none py-0"
                />
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.hazardCategories} layout="vertical" margin={CHART_MARGIN}>
                    <CartesianGrid horizontal={false} stroke="var(--color-border)" />
                    <XAxis type="number" stroke="var(--color-text-muted)" fontSize={12} tickLine={false} allowDecimals={false} />
                    <YAxis
                      type="category"
                      dataKey="category"
                      tickFormatter={(value) => RISK_CATEGORY_LABEL[value as keyof typeof RISK_CATEGORY_LABEL]}
                      stroke="var(--color-text-muted)"
                      fontSize={12}
                      tickLine={false}
                      width={140}
                    />
                    <Tooltip
                      contentStyle={{
                        background: 'var(--color-surface)',
                        border: '1px solid var(--color-border)',
                        borderRadius: 8,
                        fontSize: 12,
                      }}
                      labelFormatter={(value) => RISK_CATEGORY_LABEL[value as keyof typeof RISK_CATEGORY_LABEL]}
                    />
                    <Bar dataKey="triggerCount" name="Triggers" fill="var(--color-accent)" radius={[0, 4, 4, 0]} maxBarSize={20} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Top Triggered Rules</CardTitle>
            </CardHeader>
            <CardContent>
              {data.topRules.length === 0 ? (
                <p className="text-sm text-text-secondary">No rules triggered across the selected period.</p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Rule</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead>Category</TableHead>
                      <TableHead>Triggers</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.topRules.map((rule) => (
                      <TableRow key={rule.ruleId}>
                        <TableCell className="font-mono text-xs text-text-secondary">{rule.ruleId}</TableCell>
                        <TableCell>{rule.description}</TableCell>
                        <TableCell className="text-text-secondary">{RISK_CATEGORY_LABEL[rule.category]}</TableCell>
                        <TableCell>{rule.triggerCount}</TableCell>
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
