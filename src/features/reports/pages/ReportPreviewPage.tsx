import { useEffect, useRef, useState, type ReactNode } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Bar, BarChart, CartesianGrid, Cell, Tooltip, XAxis, YAxis } from 'recharts'
import { ArrowLeft, FileDown, Loader2, WifiOff } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Skeleton } from '@/components/ui/Skeleton'
import { EmptyState } from '@/components/ui/EmptyState'
import { ROUTES } from '@/app/routes'
import { fetchPlantState } from '@/features/plant/services/plantService'
import { incidentClassificationLabel } from '@/features/incidents/utils/incidentDisplay'
import type { IncidentClassification } from '@/features/incidents/types/incident'
import { computeAnalyticsRange } from '../context/AnalyticsRangeContext'
import { fetchIncidentResponse, fetchSafetyTrend, fetchZoneHazardReport } from '../services/reportService'
import type { IncidentResponseReport, SafetyTrendReport, ZoneHazardReport } from '../types/reports'
import { RISK_CATEGORY_LABEL, formatDateRange, formatHours } from '../utils/reportDisplay'

/**
 * A report is a frozen snapshot of one specific window — not a live view of whatever the
 * global range selector currently shows. since/until/label travel via the URL (set by
 * AnalyticsLayout's "Generate Report" action) so this page always renders exactly the period
 * that was active when it was generated, even if the user later changes the selector elsewhere.
 */
const FALLBACK_RANGE = computeAnalyticsRange('30d')

// Fixed light-theme hex values (mirroring src/styles/globals.css's :root tokens) — this document
// must render identically regardless of the viewer's current app theme, since it's captured
// verbatim into a PDF that's meant to look like a printed report, not a themed UI screenshot.
const DOC_COLOR = {
  danger: '#c0362c',
  success: '#17824e',
  warning: '#a3620a',
  info: '#2f6feb',
  accent: '#2f6feb',
  gridLine: '#e3e5e9',
  axisText: '#8b909a',
}

const CLASSIFICATION_ORDER: IncidentClassification[] = [
  'operational_episode',
  'near_miss',
  'safety_incident',
  'reportable_incident',
]

const CLASSIFICATION_COLOR: Record<IncidentClassification, string> = {
  operational_episode: DOC_COLOR.info,
  near_miss: DOC_COLOR.warning,
  safety_incident: DOC_COLOR.warning,
  reportable_incident: DOC_COLOR.danger,
}

function buildExecutiveSummary(
  trend: SafetyTrendReport,
  zoneHazard: ZoneHazardReport,
  incidentResponse: IncidentResponseReport,
): string {
  const sentences: string[] = [trend.trendSummary]

  sentences.push(
    `${trend.totalIncidentsOpened} incident${trend.totalIncidentsOpened === 1 ? '' : 's'} opened and ` +
      `${trend.totalIncidentsResolved} resolved during this period.`,
  )

  const topZone = zoneHazard.zones[0]
  if (topZone && topZone.incidentCount > 0) {
    sentences.push(
      `${topZone.zoneName} recorded the most activity, with ${topZone.incidentCount} incident${topZone.incidentCount === 1 ? '' : 's'}.`,
    )
  }

  const topHazard = zoneHazard.hazardCategories[0]
  if (topHazard) {
    sentences.push(
      `${RISK_CATEGORY_LABEL[topHazard.category]} was the most frequently triggered hazard category (${topHazard.triggerCount} triggers).`,
    )
  }

  if (incidentResponse.incidentsResolvedCount > 0) {
    sentences.push(`Incidents were resolved in a mean time of ${formatHours(incidentResponse.meanTimeToResolveHours)}.`)
  }

  return sentences.join(' ')
}

export function ReportPreviewPage() {
  const [searchParams] = useSearchParams()
  const since = searchParams.get('since') ?? FALLBACK_RANGE.since
  const until = searchParams.get('until') ?? FALLBACK_RANGE.until
  const rangeLabel = searchParams.get('label') ?? FALLBACK_RANGE.label

  const [plantName, setPlantName] = useState('Refinery')
  const [trend, setTrend] = useState<SafetyTrendReport | null>(null)
  const [zoneHazard, setZoneHazard] = useState<ZoneHazardReport | null>(null)
  const [incidentResponse, setIncidentResponse] = useState<IncidentResponseReport | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [isExporting, setIsExporting] = useState(false)

  const documentRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    let cancelled = false
    setIsLoading(true)

    Promise.all([
      fetchSafetyTrend({ since, until }),
      fetchZoneHazardReport({ since, until }),
      fetchIncidentResponse({ since, until }),
      fetchPlantState(),
    ])
      .then(([trendReport, zoneHazardReport, incidentResponseReport, state]) => {
        if (cancelled) return
        setTrend(trendReport)
        setZoneHazard(zoneHazardReport)
        setIncidentResponse(incidentResponseReport)
        setPlantName(state.plant.name)
        setError(null)
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err : new Error('Failed to load report data'))
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [since, until])

  async function handleDownloadPdf() {
    if (!documentRef.current) return
    setIsExporting(true)
    try {
      // html2canvas-pro, not plain html2canvas: this app's Tailwind v4 stylesheet uses oklch()
      // colors, which stock html2canvas's CSS parser throws on ("unsupported color function
      // oklch") — html2canvas-pro is the maintained fork that adds oklch/oklab/lab/lch support.
      const [{ default: html2canvas }, { jsPDF }] = await Promise.all([import('html2canvas-pro'), import('jspdf')])
      const canvas = await html2canvas(documentRef.current, {
        scale: 1.5,
        backgroundColor: '#ffffff',
        useCORS: true,
      })

      const pdf = new jsPDF({ orientation: 'portrait', unit: 'pt', format: 'a4' })
      const pageWidth = pdf.internal.pageSize.getWidth()
      const pageHeight = pdf.internal.pageSize.getHeight()
      const imgWidth = pageWidth
      const imgHeight = (canvas.height * imgWidth) / canvas.width
      // JPEG at 0.85 quality, not PNG: this is a raster capture of a mostly-flat, mostly-text
      // document, so PNG's lossless encoding just inflates file size for no visible benefit —
      // "lightweight" per the brief, and a multi-page PNG capture ran ~15MB versus ~1-2MB here.
      const imgData = canvas.toDataURL('image/jpeg', 0.85)

      let heightLeft = imgHeight
      let position = 0
      pdf.addImage(imgData, 'JPEG', 0, position, imgWidth, imgHeight)
      heightLeft -= pageHeight

      while (heightLeft > 0) {
        position -= pageHeight
        pdf.addPage()
        pdf.addImage(imgData, 'JPEG', 0, position, imgWidth, imgHeight)
        heightLeft -= pageHeight
      }

      const datePart = new Date().toISOString().slice(0, 10)
      pdf.save(`safety-analytics-report-${datePart}.pdf`)
    } finally {
      setIsExporting(false)
    }
  }

  const topZones = zoneHazard ? [...zoneHazard.zones].sort((a, b) => b.incidentCount - a.incidentCount).slice(0, 5) : []
  const trendChartData = trend?.periods ?? []
  const classificationChartData = incidentResponse
    ? CLASSIFICATION_ORDER.map((classification) => ({
        classification,
        label: incidentClassificationLabel(classification),
        count: incidentResponse.classificationBreakdown.find((entry) => entry.classification === classification)?.count ?? 0,
      }))
    : []

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Link
          to={ROUTES.reports}
          className="inline-flex w-fit items-center gap-1.5 text-sm text-text-secondary transition-colors hover:text-text-primary"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          Safety Analytics
        </Link>
        {trend && zoneHazard && incidentResponse && (
          <Button size="sm" onClick={handleDownloadPdf} isLoading={isExporting}>
            {!isExporting && <FileDown className="h-3.5 w-3.5" aria-hidden="true" />}
            {isExporting ? 'Preparing PDF…' : 'Download PDF'}
          </Button>
        )}
      </div>

      {isLoading ? (
        <Skeleton className="h-[900px]" />
      ) : error || !trend || !zoneHazard || !incidentResponse ? (
        <EmptyState
          icon={WifiOff}
          title="Can't generate this report"
          description="The reporting service isn't responding. Make sure the backend is running, then try again."
        />
      ) : (
        <div
          ref={documentRef}
          className="mx-auto w-full max-w-3xl rounded-lg border border-gray-200 bg-white p-10 text-gray-900"
          style={{ colorScheme: 'light' }}
        >
          <header className="mb-8 flex items-start justify-between gap-4 border-b border-gray-200 pb-6">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                Safety Analytics Report
              </p>
              <h1 className="mt-1 text-2xl font-bold text-gray-900">{plantName}</h1>
              <p className="mt-1.5 text-sm text-gray-500">
                {rangeLabel} · {formatDateRange(since, until)}
              </p>
            </div>
            <p className="shrink-0 text-right text-xs text-gray-400">
              Generated
              <br />
              {new Date().toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })}
            </p>
          </header>

          <Section title="Executive Summary">
            <p className="text-sm leading-relaxed text-gray-700">
              {buildExecutiveSummary(trend, zoneHazard, incidentResponse)}
            </p>
          </Section>

          <Section title="Key Metrics">
            <div className="grid grid-cols-3 gap-3">
              <Metric label="Incidents Opened" value={String(trend.totalIncidentsOpened)} />
              <Metric label="Incidents Resolved" value={String(trend.totalIncidentsResolved)} />
              <Metric label="Mean Time to Resolve" value={formatHours(incidentResponse.meanTimeToResolveHours)} />
              <Metric label="Zones with Incidents" value={String(zoneHazard.zones.filter((z) => z.incidentCount > 0).length)} />
              <Metric
                label="Top Hazard"
                value={zoneHazard.hazardCategories[0] ? RISK_CATEGORY_LABEL[zoneHazard.hazardCategories[0].category] : '—'}
              />
              <Metric label="Recommendations Acknowledged" value={String(incidentResponse.recommendationsAcknowledgedCount)} />
            </div>
          </Section>

          {trendChartData.length > 0 && (
            <Section title="Incidents Opened vs. Resolved">
              <BarChart width={640} height={220} data={trendChartData} barGap={2}>
                <CartesianGrid vertical={false} stroke={DOC_COLOR.gridLine} />
                <XAxis dataKey="periodStart" hide />
                <YAxis stroke={DOC_COLOR.axisText} fontSize={11} tickLine={false} allowDecimals={false} width={28} />
                <Tooltip />
                <Bar dataKey="incidentsOpened" name="Opened" fill={DOC_COLOR.danger} radius={[3, 3, 0, 0]} maxBarSize={20} />
                <Bar dataKey="incidentsResolved" name="Resolved" fill={DOC_COLOR.success} radius={[3, 3, 0, 0]} maxBarSize={20} />
              </BarChart>
            </Section>
          )}

          <Section title="Incident Summary">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-gray-200 text-xs uppercase tracking-wide text-gray-400">
                  <th className="py-1.5 font-medium">Classification</th>
                  <th className="py-1.5 text-right font-medium">Count</th>
                </tr>
              </thead>
              <tbody>
                {classificationChartData.map((row) => (
                  <tr key={row.classification} className="border-b border-gray-100 last:border-0">
                    <td className="flex items-center gap-2 py-1.5 text-gray-700">
                      <span
                        className="h-2 w-2 shrink-0 rounded-full"
                        style={{ backgroundColor: CLASSIFICATION_COLOR[row.classification] }}
                        aria-hidden="true"
                      />
                      {row.label}
                    </td>
                    <td className="py-1.5 text-right font-medium text-gray-900">{row.count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="mt-4 grid grid-cols-3 gap-3">
              <Metric label="Mean Time to Resolve" value={formatHours(incidentResponse.meanTimeToResolveHours)} />
              <Metric label="Mean Time to Close" value={formatHours(incidentResponse.meanTimeToCloseHours)} />
              <Metric
                label="Mean Time to Acknowledge"
                value={
                  incidentResponse.meanTimeToAcknowledgeMinutes == null
                    ? '—'
                    : formatHours(incidentResponse.meanTimeToAcknowledgeMinutes / 60)
                }
              />
            </div>
          </Section>

          {topZones.length > 0 && (
            <Section title="Zone Summary">
              <BarChart width={640} height={Math.max(120, topZones.length * 34)} data={topZones} layout="vertical" margin={{ top: 4, right: 24, bottom: 4, left: 4 }}>
                <CartesianGrid horizontal={false} stroke={DOC_COLOR.gridLine} />
                <XAxis type="number" stroke={DOC_COLOR.axisText} fontSize={11} tickLine={false} allowDecimals={false} />
                <YAxis type="category" dataKey="zoneName" stroke={DOC_COLOR.axisText} fontSize={11} tickLine={false} width={170} />
                <Tooltip />
                <Bar dataKey="incidentCount" name="Incidents" radius={[0, 3, 3, 0]} maxBarSize={16}>
                  {topZones.map((zone) => (
                    <Cell key={zone.zoneId} fill={zone.reportableIncidentCount > 0 ? DOC_COLOR.danger : DOC_COLOR.accent} />
                  ))}
                </Bar>
              </BarChart>
            </Section>
          )}

          <Section title="Hazard Summary" last>
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-gray-200 text-xs uppercase tracking-wide text-gray-400">
                  <th className="py-1.5 font-medium">Rule</th>
                  <th className="py-1.5 font-medium">Category</th>
                  <th className="py-1.5 text-right font-medium">Triggers</th>
                </tr>
              </thead>
              <tbody>
                {zoneHazard.topRules.slice(0, 5).map((rule) => (
                  <tr key={rule.ruleId} className="border-b border-gray-100 last:border-0">
                    <td className="py-1.5 text-gray-700">{rule.description}</td>
                    <td className="py-1.5 text-gray-500">{RISK_CATEGORY_LABEL[rule.category]}</td>
                    <td className="py-1.5 text-right font-medium text-gray-900">{rule.triggerCount}</td>
                  </tr>
                ))}
                {zoneHazard.topRules.length === 0 && (
                  <tr>
                    <td colSpan={3} className="py-3 text-center text-gray-400">
                      No hazards triggered during this period.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </Section>

          <footer className="mt-8 border-t border-gray-200 pt-4 text-center text-xs text-gray-400">
            Industrial Safety Intelligence Platform — deterministic analytics, no AI-generated content.
          </footer>
        </div>
      )}
    </div>
  )
}

function Section({ title, children, last = false }: { title: string; children: ReactNode; last?: boolean }) {
  return (
    <section className={last ? 'mb-0' : 'mb-8'}>
      <h2 className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">{title}</h2>
      {children}
    </section>
  )
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-gray-200 bg-gray-50 px-3 py-2.5">
      <p className="text-[10px] font-medium uppercase tracking-wide text-gray-400">{label}</p>
      <p className="mt-0.5 text-lg font-semibold text-gray-900">{value}</p>
    </div>
  )
}
