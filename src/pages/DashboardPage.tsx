import { LayoutDashboard } from 'lucide-react'
import { PageHeader } from '@/components/ui/PageHeader'
import { EmptyState } from '@/components/ui/EmptyState'

export function DashboardPage() {
  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Dashboard"
        description="A unified overview of plant safety operations will live here."
      />
      <EmptyState
        icon={LayoutDashboard}
        title="No dashboard data yet"
        description="This workspace is ready. Overview widgets will be added in a later phase."
      />
    </div>
  )
}
