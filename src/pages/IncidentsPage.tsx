import { AlertTriangle } from 'lucide-react'
import { PageHeader } from '@/components/ui/PageHeader'
import { EmptyState } from '@/components/ui/EmptyState'

export function IncidentsPage() {
  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Incidents"
        description="Safety incidents reported across the refinery and their resolution status will appear here."
      />
      <EmptyState
        icon={AlertTriangle}
        title="No incidents recorded"
        description="Incident tracking will be added in a later phase."
      />
    </div>
  )
}
