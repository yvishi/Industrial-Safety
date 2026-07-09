import { Search, Bell, Sun, User } from 'lucide-react'
import { useBreadcrumbs } from '@/hooks/useBreadcrumbs'
import { Breadcrumbs } from '@/components/ui/Breadcrumbs'

export function Topbar() {
  const breadcrumbs = useBreadcrumbs()

  return (
    <header className="flex h-14 shrink-0 items-center gap-4 border-b border-border bg-surface px-4 sm:px-6">
      <Breadcrumbs items={breadcrumbs} />

      <div className="ml-2 hidden max-w-md flex-1 items-center gap-2 rounded-md border border-border bg-surface-sunken px-3 py-1.5 text-sm text-text-muted sm:flex">
        <Search className="h-4 w-4 shrink-0" aria-hidden="true" />
        <span className="truncate">Search…</span>
        <kbd className="ml-auto shrink-0 rounded border border-border bg-surface px-1.5 py-0.5 text-xs text-text-muted">
          ⌘K
        </kbd>
      </div>

      <div className="ml-auto flex items-center gap-1">
        <button
          type="button"
          className="flex h-8 w-8 items-center justify-center rounded-md text-text-secondary transition-colors hover:bg-surface-hover hover:text-text-primary"
          aria-label="Toggle theme"
        >
          <Sun className="h-4 w-4" aria-hidden="true" />
        </button>
        <button
          type="button"
          className="relative flex h-8 w-8 items-center justify-center rounded-md text-text-secondary transition-colors hover:bg-surface-hover hover:text-text-primary"
          aria-label="Notifications"
        >
          <Bell className="h-4 w-4" aria-hidden="true" />
          <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-accent" aria-hidden="true" />
        </button>
        <button
          type="button"
          className="ml-1 flex h-8 w-8 items-center justify-center rounded-full bg-surface-sunken text-text-secondary transition-colors hover:bg-surface-hover"
          aria-label="User profile"
        >
          <User className="h-4 w-4" aria-hidden="true" />
        </button>
      </div>
    </header>
  )
}
