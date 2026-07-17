import { Link } from 'react-router-dom'
import { ActivitySquare, MapPinned, Timer, type LucideIcon } from 'lucide-react'
import { PageHeader } from '@/components/ui/PageHeader'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { ROUTES } from '@/app/routes'

interface ReportLink {
  to: string
  icon: LucideIcon
  title: string
  description: string
}

const REPORTS: ReportLink[] = [
  {
    to: `${ROUTES.reports}/safety-trend`,
    icon: ActivitySquare,
    title: 'Safety Trend',
    description: 'Is the refinery becoming safer over time — incident volume and risk-level mix, period over period.',
  },
  {
    to: `${ROUTES.reports}/zones-hazards`,
    icon: MapPinned,
    title: 'Zones & Hazards',
    description: 'Which zones and hazard categories need attention, ranked by incident and trigger counts.',
  },
  {
    to: `${ROUTES.reports}/incident-response`,
    icon: Timer,
    title: 'Incident Response',
    description: 'How fast the team resolves incidents and acts on recommendations, by classification.',
  },
]

export function ReportsHubPage() {
  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Reports & Analytics"
        description="Historical trends and analysis across the plant."
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {REPORTS.map(({ to, icon: Icon, title, description }) => (
          <Link key={to} to={to} className="block">
            <Card className="h-full transition-colors hover:border-border-strong hover:bg-surface-hover">
              <CardHeader className="flex-row items-center gap-3 border-b-0">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-accent-subtle">
                  <Icon className="h-4 w-4 text-accent" aria-hidden="true" />
                </div>
                <CardTitle>{title}</CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                <p className="text-sm text-text-secondary">{description}</p>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}
