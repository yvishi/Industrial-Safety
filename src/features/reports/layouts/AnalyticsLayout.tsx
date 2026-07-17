import { Link, Outlet, useNavigate } from 'react-router-dom'
import { ArrowLeft, FileOutput } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { ROUTES, buildReportPreviewPath } from '@/app/routes'
import { AnalyticsRangeProvider, useAnalyticsRange } from '../context/AnalyticsRangeContext'
import { AnalyticsRangeSelector } from '../components/AnalyticsRangeSelector'

/**
 * Shared shell for every Safety Analytics page (Safety Trend / Zones & Hazards / Incident
 * Response): one time-range control and one "Generate Report" action, instead of each page
 * duplicating its own filter bar. The selected range flows down via AnalyticsRangeProvider, and
 * "Generate Report" hands the exact range that produced what's on screen to the Preview page —
 * a report always reflects the range that was active when it was generated, not whatever the
 * selector happens to show later.
 */
export function AnalyticsLayout() {
  return (
    <AnalyticsRangeProvider>
      <AnalyticsLayoutContent />
    </AnalyticsRangeProvider>
  )
}

function AnalyticsLayoutContent() {
  const { range } = useAnalyticsRange()
  const navigate = useNavigate()

  return (
    <div className="flex flex-col gap-6">
      <Link
        to={ROUTES.reports}
        className="inline-flex w-fit items-center gap-1.5 text-sm text-text-secondary transition-colors hover:text-text-primary"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden="true" />
        Safety Analytics
      </Link>

      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-5">
        <AnalyticsRangeSelector />
        <Button
          size="sm"
          onClick={() =>
            navigate(buildReportPreviewPath({ since: range.since, until: range.until, label: range.label }))
          }
        >
          <FileOutput className="h-3.5 w-3.5" aria-hidden="true" />
          Generate Report
        </Button>
      </div>

      <Outlet />
    </div>
  )
}
