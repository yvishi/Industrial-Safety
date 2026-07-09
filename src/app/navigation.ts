import {
  LayoutDashboard,
  Factory,
  AlertTriangle,
  History,
  FileText,
  Settings,
} from 'lucide-react'
import type { NavItem } from '@/types/navigation'
import { ROUTES } from './routes'

/** Single source of truth for the primary navigation, consumed by the Sidebar and Topbar. */
export const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', path: ROUTES.dashboard, icon: LayoutDashboard },
  { label: 'Plant', path: ROUTES.plant, icon: Factory },
  { label: 'Incidents', path: ROUTES.incidents, icon: AlertTriangle },
  { label: 'Timeline', path: ROUTES.timeline, icon: History },
  { label: 'Reports', path: ROUTES.reports, icon: FileText },
  { label: 'Settings', path: ROUTES.settings, icon: Settings },
]
