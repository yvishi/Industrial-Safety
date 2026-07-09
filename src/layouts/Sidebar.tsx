import { NavLink } from 'react-router-dom'
import { ChevronsLeft, ChevronsRight, ShieldCheck } from 'lucide-react'
import { NAV_ITEMS } from '@/app/navigation'
import { cn } from '@/utils/cn'

export interface SidebarProps {
  isCollapsed: boolean
  onToggleCollapse: () => void
}

export function Sidebar({ isCollapsed, onToggleCollapse }: SidebarProps) {
  return (
    <aside
      className={cn(
        'flex h-full shrink-0 flex-col border-r border-border bg-surface transition-[width] duration-150 ease-out',
        isCollapsed ? 'w-16' : 'w-64',
      )}
    >
      {/* Logo */}
      <div className="flex h-14 shrink-0 items-center gap-2 border-b border-border px-4">
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-accent text-accent-fg">
          <ShieldCheck className="h-4 w-4" aria-hidden="true" />
        </div>
        {!isCollapsed && (
          <span className="truncate text-sm font-semibold text-text-primary">
            Industrial Safety
          </span>
        )}
      </div>

      {/* Primary navigation */}
      <nav className="flex flex-1 flex-col gap-1 overflow-y-auto p-2">
        {NAV_ITEMS.map(({ label, path, icon: Icon }) => (
          <NavLink
            key={path}
            to={path}
            end={path === '/'}
            title={isCollapsed ? label : undefined}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-md px-2.5 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-accent-subtle text-accent'
                  : 'text-text-secondary hover:bg-surface-hover hover:text-text-primary',
                isCollapsed && 'justify-center',
              )
            }
          >
            <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
            {!isCollapsed && <span className="truncate">{label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Collapse toggle */}
      <button
        type="button"
        onClick={onToggleCollapse}
        className={cn(
          'flex items-center gap-2 border-t border-border px-4 py-3 text-sm text-text-secondary transition-colors hover:bg-surface-hover hover:text-text-primary',
          isCollapsed && 'justify-center',
        )}
        aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        {isCollapsed ? <ChevronsRight className="h-4 w-4" /> : <ChevronsLeft className="h-4 w-4" />}
        {!isCollapsed && <span>Collapse</span>}
      </button>

      {/* Profile */}
      <div
        className={cn(
          'flex items-center gap-3 border-t border-border px-4 py-3',
          isCollapsed && 'justify-center px-2',
        )}
      >
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-surface-sunken text-xs font-semibold text-text-secondary">
          JD
        </div>
        {!isCollapsed && (
          <div className="flex min-w-0 flex-col">
            <span className="truncate text-sm font-medium text-text-primary">Jordan Diaz</span>
            <span className="truncate text-xs text-text-muted">Safety Officer</span>
          </div>
        )}
      </div>
    </aside>
  )
}
