import { createBrowserRouter } from 'react-router-dom'
import { AppLayout } from '@/layouts/AppLayout'
import {
  DashboardPage,
  PlantPage,
  IncidentsPage,
  TimelinePage,
  ReportsPage,
  SettingsPage,
  NotFoundPage,
} from '@/pages'
import { ROUTES } from './routes'

export const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      { path: ROUTES.dashboard, element: <DashboardPage /> },
      { path: ROUTES.plant, element: <PlantPage /> },
      { path: ROUTES.incidents, element: <IncidentsPage /> },
      { path: ROUTES.timeline, element: <TimelinePage /> },
      { path: ROUTES.reports, element: <ReportsPage /> },
      { path: ROUTES.settings, element: <SettingsPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
])
