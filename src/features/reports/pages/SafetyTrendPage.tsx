import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { ArrowLeft, ClipboardCheck, ClipboardList, TrendingUp, WifiOff } from 'lucide-react'
import { PageHeader } from '@/components/ui/PageHeader'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Skeleton } from '@/components/ui/Skeleton'
import { EmptyState } from '@/components/ui/EmptyState'
import { ROUTES } from '@/app/routes'
import { DateRangeFilter, computeRange, type DateRange } from '../components/DateRangeFilter'
import { ReportKpiTile } from '../components/ReportKpiTile'
import { useReportFetch } from '../hooks/useReportFetch'
import { fetchSafetyTrend } from '../services/reportService'
import { formatPeriodLabel, trendDirectionLabel, trendDirectionStatus } from '../utils/reportDisplay'

const RISK_LEVEL_SERIES: Array<{
  key: 'normalCount' | 'lowCount' | 'moderateCount' | 'highCount' | 'criticalCount'
  label: string
  color: string
  fillOpacity?: number
}> = [
  { key: 'normalCount', label: 'Normal', color: 'var(--color-success)' },
  { key: 'lowCount', label: 'Low', color: 'var(--color-info)' },
  { key: 'moderateCount', label: 'Moderate', color: 'var(--color-warning)', fillOpacity: 0.55 },
  { key: 'highCount', label: 'High', color: 'var(--color-warning)' },
  { key: 'criticalCount', label: 'Critical', color: 'var(--color-danger)' },
]

/** "Is the refinery becoming safer?" — incident volume and risk-level mix over time. */
export function SafetyTrendPage() {
  const [range, setRange] = useState<DateRange>(() => computeRange(30))

  const { data, error, isLoading } = useReportFetch(
    () => fetchSafetyTrend({ since: range.since, until: range.until }),
    [range.since, range.until],
  )

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
        title="Safety Trend"
        description="Incident volume and risk-level mix over time — is the refinery becoming safer?"
      />

      <DateRangeFilter onChange={setRange} />

      {isLoading ? (
        <div className="flex flex-col gap-4">
          <div className="grid gap-4 sm:grid-cols-3">
            <Skeleton className="h-24" />
            <Skeleton className="h-24" />
            <Skeleton className="h-24" />
          </div>
          <Skeleton className="h-72" />
          <Skeleton className="h-72" />
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
              label="Incidents Opened"
              value={data.totalIncidentsOpened}
              icon={ClipboardList}
            />
            <ReportKpiTile
              label="Incidents Resolved"
              value={data.totalIncidentsResolved}
              icon={ClipboardCheck}
              tone="success"
            />
            <ReportKpiTile
              label="Trend"
              value={trendDirectionLabel(data.trendDirection)}
              sublabel={data.trendSummary}
              icon={TrendingUp}
              tone={
                data.trendDirection === 'up' ? 'danger' : data.trendDirection === 'down' ? 'success' : 'neutral'
              }
            />
          </div>

          {data.periods.every((p) => p.incidentsOpened === 0 && p.incidentsResolved === 0) ? (
            <EmptyState
              icon={TrendingUp}
              title="No incidents in this range"
              description="Nothing was opened or resolved across the selected period."
            />
          ) : (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>Incidents Opened vs. Resolved</CardTitle>
                </CardHeader>
                <CardContent className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data.periods} barGap={2}>
                      <CartesianGrid vertical={false} stroke="var(--color-border)" />
                      <XAxis
                        dataKey="periodStart"
                        tickFormatter={(value) => formatPeriodLabel(value, data.periodGranularity)}
                        stroke="var(--color-text-muted)"
                        fontSize={12}
                        tickLine={false}
                      />
                      <YAxis stroke="var(--color-text-muted)" fontSize={12} tickLine={false} allowDecimals={false} />
                      <Tooltip
                        contentStyle={{
                          background: 'var(--color-surface)',
                          border: '1px solid var(--color-border)',
                          borderRadius: 8,
                          fontSize: 12,
                        }}
                        labelFormatter={(value) => formatPeriodLabel(value as string, data.periodGranularity)}
                      />
                      <Legend
                        wrapperStyle={{ fontSize: 12 }}
                        itemSorter={(item) => (item.value === 'Opened' ? 0 : 1)}
                      />
                      <Bar dataKey="incidentsOpened" name="Opened" fill="var(--color-danger)" radius={[4, 4, 0, 0]} maxBarSize={24} />
                      <Bar dataKey="incidentsResolved" name="Resolved" fill="var(--color-success)" radius={[4, 4, 0, 0]} maxBarSize={24} />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Risk Level Mix</CardTitle>
                </CardHeader>
                <CardContent className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data.periods}>
                      <CartesianGrid vertical={false} stroke="var(--color-border)" />
                      <XAxis
                        dataKey="periodStart"
                        tickFormatter={(value) => formatPeriodLabel(value, data.periodGranularity)}
                        stroke="var(--color-text-muted)"
                        fontSize={12}
                        tickLine={false}
                      />
                      <YAxis stroke="var(--color-text-muted)" fontSize={12} tickLine={false} allowDecimals={false} />
                      <Tooltip
                        contentStyle={{
                          background: 'var(--color-surface)',
                          border: '1px solid var(--color-border)',
                          borderRadius: 8,
                          fontSize: 12,
                        }}
                        labelFormatter={(value) => formatPeriodLabel(value as string, data.periodGranularity)}
                      />
                      <Legend
                        wrapperStyle={{ fontSize: 12 }}
                        itemSorter={(item) => RISK_LEVEL_SERIES.findIndex((series) => series.label === item.value)}
                      />
                      {RISK_LEVEL_SERIES.map((series) => (
                        <Bar
                          key={series.key}
                          dataKey={series.key}
                          name={series.label}
                          stackId="risk"
                          fill={series.color}
                          fillOpacity={series.fillOpacity}
                          maxBarSize={24}
                        />
                      ))}
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </>
          )}
        </>
      )}
    </div>
  )
}
