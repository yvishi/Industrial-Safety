import { Link } from 'react-router-dom'
import { Compass } from 'lucide-react'
import { EmptyState } from '@/components/ui/EmptyState'
import { buttonVariants } from '@/components/ui/Button'
import { ROUTES } from '@/app/routes'

export function NotFoundPage() {
  return (
    <div className="flex h-full min-h-[60vh] items-center justify-center">
      <EmptyState
        icon={Compass}
        title="404 — Page not found"
        description="The page you're looking for doesn't exist or has been moved."
        action={
          <Link to={ROUTES.dashboard} className={buttonVariants({ variant: 'secondary', size: 'sm' })}>
            Back to Dashboard
          </Link>
        }
      />
    </div>
  )
}
