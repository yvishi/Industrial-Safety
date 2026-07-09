import { createBrowserRouter, Outlet } from 'react-router-dom'
import { AppLayout } from '@/layouts/AppLayout'
import {
  DashboardPage,
  IncidentsPage,
  TimelinePage,
  ReportsPage,
  SettingsPage,
  NotFoundPage,
} from '@/pages'
import { PlantOverviewPage, ZoneDetailPage } from '@/features/plant'
import { getZoneById } from '@/features/plant/data/zones'
import { ROUTES } from './routes'

export const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      { path: ROUTES.dashboard, element: <DashboardPage />, handle: { crumb: () => 'Dashboard' } },
      {
        path: ROUTES.plant,
        element: <Outlet />,
        handle: { crumb: () => 'Plant' },
        children: [
          { index: true, element: <PlantOverviewPage /> },
          {
            path: 'zones/:zoneId',
            element: <ZoneDetailPage />,
            handle: {
              crumb: (params: Record<string, string | undefined>) =>
                (params.zoneId && getZoneById(params.zoneId)?.name) || 'Zone',
            },
          },
        ],
      },
      { path: ROUTES.incidents, element: <IncidentsPage />, handle: { crumb: () => 'Incidents' } },
      { path: ROUTES.timeline, element: <TimelinePage />, handle: { crumb: () => 'Timeline' } },
      { path: ROUTES.reports, element: <ReportsPage />, handle: { crumb: () => 'Reports' } },
      { path: ROUTES.settings, element: <SettingsPage />, handle: { crumb: () => 'Settings' } },
      { path: '*', element: <NotFoundPage />, handle: { crumb: () => 'Not Found' } },
    ],
  },
])
