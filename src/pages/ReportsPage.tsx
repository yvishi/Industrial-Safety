import { FileText } from 'lucide-react'
import { PageHeader } from '@/components/ui/PageHeader'
import { EmptyState } from '@/components/ui/EmptyState'

export function ReportsPage() {
  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Reports"
        description="Compliance and safety reports will be generated and archived here."
      />
      <EmptyState
        icon={FileText}
        title="No reports yet"
        description="Reporting tools will be added in a later phase."
      />
    </div>
  )
}
