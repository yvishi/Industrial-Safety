import { Settings } from 'lucide-react'
import { PageHeader } from '@/components/ui/PageHeader'
import { EmptyState } from '@/components/ui/EmptyState'

export function SettingsPage() {
  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Settings"
        description="Workspace, user, and platform configuration will be managed here."
      />
      <EmptyState
        icon={Settings}
        title="No settings configured yet"
        description="Configuration options will be added in a later phase."
      />
    </div>
  )
}
