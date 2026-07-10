import { History } from 'lucide-react'
import { PageHeader } from '@/components/ui/PageHeader'
import { EmptyState } from '@/components/ui/EmptyState'

export function TimelinePage() {
  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Timeline"
        description="A chronological record of refinery events and operational changes will appear here."
      />
      <EmptyState
        icon={History}
        title="No timeline events yet"
        description="Event history will be added in a later phase."
      />
    </div>
  )
}
