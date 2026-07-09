import { useEffect, useState } from 'react'
import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Topbar } from './Topbar'
import { useMediaQuery } from '@/hooks/useMediaQuery'

export function AppLayout() {
  const isNarrowViewport = useMediaQuery('(max-width: 1024px)')
  const [isCollapsed, setIsCollapsed] = useState(isNarrowViewport)

  // Auto-collapse on smaller viewports, but leave manual toggles on desktop alone.
  useEffect(() => {
    setIsCollapsed(isNarrowViewport)
  }, [isNarrowViewport])

  return (
    <div className="flex h-screen w-full overflow-hidden bg-bg">
      <Sidebar isCollapsed={isCollapsed} onToggleCollapse={() => setIsCollapsed((prev) => !prev)} />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar />
        <main className="flex-1 overflow-y-auto px-4 py-6 sm:px-6 lg:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
