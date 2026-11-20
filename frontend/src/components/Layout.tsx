import { useEffect } from 'react'
import { Link, NavLink, Navigate, Outlet, useLocation } from 'react-router'
import { useSession } from '../auth/session'
import { useOnline } from '../hooks/useOnline'
import { useOutbox } from '../offline/progress'
import { onSyncNotice } from '../offline/sync'
import { Icon, type IconName } from './Icon'
import { SyncIndicator } from './SyncIndicator'
import { toast } from './toast'

const TABS: { to: string; label: string; icon: IconName; end?: boolean }[] = [
  { to: '/', label: 'Home', icon: 'home', end: true },
  { to: '/roadmaps', label: 'Roadmaps', icon: 'map' },
  { to: '/library', label: 'Library', icon: 'book' },
  { to: '/progress', label: 'Progress', icon: 'chart' },
  { to: '/profile', label: 'Profile', icon: 'user' },
]

export function Layout() {
  const online = useOnline()
  const session = useSession()
  const pending = useOutbox().length
  const { pathname } = useLocation()

  useEffect(() => {
    const unsubscribe = onSyncNotice((message) => toast(message, 'error'))
    return unsubscribe
  }, [])
  // Block body on purpose: newer browsers return a Promise from scrollTo(), and
  // React would take any returned value as the effect's cleanup and call it.
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])

  return (
    <div className="app">
      <aside className="sidebar">
        <Link to="/" className="brand">
          <img src="/icons/icon.svg" alt="" width={32} height={32} />
          <span>Learning Roadmap</span>
        </Link>
        <nav>
          {TABS.map((tab) => (
            <NavLink key={tab.to} to={tab.to} end={tab.end} className="side-link">
              <Icon name={tab.icon} />
              {tab.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-foot">
          <SyncIndicator />
          <span className="muted small">{online ? 'Online' : 'Offline'}</span>
        </div>
      </aside>
      <div className="main">
        {!online && (
          <div className="banner banner-offline">
            <Icon name="offline" size={16} />
            You're offline.{' '}
            {pending
              ? `${pending} change(s) will sync when you reconnect.`
              : 'Saved roadmaps, progress and downloaded files still work.'}
          </div>
        )}
        {session?.expired && (
          <div className="banner banner-warning">
            Your session expired.{' '}
            <Link to="/login" state={{ from: pathname }}>
              Sign in again
            </Link>{' '}
            to sync{pending ? ` ${pending} pending change(s)` : ''}.
          </div>
        )}
        <Outlet />
      </div>
      <nav className="tabbar">
        {TABS.map((tab) => (
          <NavLink key={tab.to} to={tab.to} end={tab.end} className="tab">
            <Icon name={tab.icon} size={22} />
            <span>{tab.label}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  )
}

export function RequireAuth() {
  const session = useSession()
  const location = useLocation()
  if (!session) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  return <Outlet />
}
