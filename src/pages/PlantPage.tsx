import { Factory } from 'lucide-react'
import { PageHeader } from '@/components/ui/PageHeader'
import { EmptyState } from '@/components/ui/EmptyState'

export function PlantPage() {
  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Plant"
        description="Facility layout, zones, and equipment registry will be managed here."
      />
      <EmptyState
        icon={Factory}
        title="No plant data yet"
        description="Facility structure will be configured in a later phase."
      />
    </div>
  )
}
