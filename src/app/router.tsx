import { createBrowserRouter, Outlet } from 'react-router-dom'
import { AppLayout } from '@/layouts/AppLayout'
import {
  DashboardPage,
  ReportsPage,
  SettingsPage,
  NotFoundPage,
} from '@/pages'
import { PlantOverviewPage, ZoneDetailPage } from '@/features/plant'
import { IncidentsListPage, IncidentDetailPage, TimelinePage } from '@/features/incidents'
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
            // Zone data loads async from the API — ZoneDetailPage overrides this via
            // useBreadcrumbLabel once the zone name is known.
            handle: { crumb: () => 'Zone' },
          },
        ],
      },
      {
        path: ROUTES.incidents,
        element: <Outlet />,
        handle: { crumb: () => 'Incidents' },
        children: [
          { index: true, element: <IncidentsListPage /> },
          {
            path: ':incidentId',
            element: <IncidentDetailPage />,
            // Incident data loads async — IncidentDetailPage overrides this via
            // useBreadcrumbLabel once the incident's title is known.
            handle: { crumb: () => 'Incident' },
          },
        ],
      },
      { path: ROUTES.timeline, element: <TimelinePage />, handle: { crumb: () => 'Timeline' } },
      { path: ROUTES.reports, element: <ReportsPage />, handle: { crumb: () => 'Reports' } },
      { path: ROUTES.settings, element: <SettingsPage />, handle: { crumb: () => 'Settings' } },
      { path: '*', element: <NotFoundPage />, handle: { crumb: () => 'Not Found' } },
    ],
  },
])
