import { useNavigate } from 'react-router'
import { useSession } from '../auth/session'
import { followRoadmap, useLocalProgress } from '../offline/progress'
import { toast } from './toast'

/** Follow a roadmap (works offline; synced later). Signed-out users go to sign-in. */
export function FollowButton({
  roadmap,
  className = 'btn btn-primary',
  label = 'Start this roadmap',
}: {
  roadmap: { id: number; name: string }
  className?: string
  label?: string
}) {
  const session = useSession()
  const navigate = useNavigate()
  const { known } = useLocalProgress()
  // Signed in but enrollments not loaded yet: don't offer "Start" to someone
  // who may already follow the roadmap.
  if (session && !known) return null
  return (
    <button
      className={className}
      onClick={async () => {
        if (!session) {
          navigate('/login', { state: { from: `/roadmaps/${roadmap.id}` } })
          return
        }
        await followRoadmap(roadmap.id, roadmap.name)
        toast(
          navigator.onLine ? `You're following “${roadmap.name}”.` : `Following “${roadmap.name}” (will sync when online).`,
          'success',
        )
      }}
    >
      {label}
    </button>
  )
}
