// Small shared presentational components.
import type { ReactNode } from 'react'
import { Link, useNavigate } from 'react-router'
import type { Progress } from '../api/types'
import { Icon, type IconName } from './Icon'
import { SyncIndicator } from './SyncIndicator'

export function Page({
  title,
  subtitle,
  back,
  actions,
  children,
  wide,
}: {
  title: ReactNode
  subtitle?: ReactNode
  /** Back target (path), or true for history back. */
  back?: string | true
  actions?: ReactNode
  children: ReactNode
  wide?: boolean
}) {
  const navigate = useNavigate()
  return (
    <>
      <header className="topbar">
        {back && (
          <button
            className="icon-btn"
            aria-label="Back"
            onClick={() => (back === true ? navigate(-1) : navigate(back))}
          >
            <Icon name="back" size={22} />
          </button>
        )}
        <div className="topbar-title">
          <h1>{title}</h1>
          {subtitle && <div className="topbar-subtitle">{subtitle}</div>}
        </div>
        <div className="topbar-actions">
          {actions}
          <span className="mobile-only">
            <SyncIndicator />
          </span>
        </div>
      </header>
      <main className={`content${wide ? ' content-wide' : ''}`}>{children}</main>
    </>
  )
}

export function ProgressBar({ value, label }: { value: number; label?: string }) {
  return (
    <div
      className="progress"
      role="progressbar"
      aria-valuenow={value}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={label}
    >
      <div className="progress-fill" style={{ width: `${value}%` }} />
    </div>
  )
}

export function ProgressRing({ value, size = 56 }: { value: number; size?: number }) {
  const r = 15.9155
  return (
    <div className="ring" style={{ width: size, height: size }}>
      <svg viewBox="0 0 36 36" width={size} height={size}>
        <circle className="ring-track" cx="18" cy="18" r={r} />
        {value > 0 && <circle
          className="ring-fill"
          cx="18"
          cy="18"
          r={r}
          strokeDasharray={`${value} 100`}
          transform="rotate(-90 18 18)"
        />}
      </svg>
      <span className="ring-label">{value}%</span>
    </div>
  )
}

export function ProgressSummary({ progress, label }: { progress: Progress; label?: string }) {
  return (
    <div className="progress-summary">
      <div className="progress-summary-row">
        <span>{progress.percent === 100 ? 'Completed' : (label ?? 'Progress')}</span>
        <span className="muted">
          {progress.completed} / {progress.total} topics · {progress.percent}%
        </span>
      </div>
      <ProgressBar value={progress.percent} label={label} />
    </div>
  )
}

/** Server-sanitized rich text (nh3 allowlist on the backend). */
export function Rich({ html, className = '' }: { html: string; className?: string }) {
  if (!html) return null
  return <div className={`rich ${className}`} dangerouslySetInnerHTML={{ __html: html }} />
}

export function Empty({
  icon = 'list',
  title,
  children,
}: {
  icon?: IconName
  title: string
  children?: ReactNode
}) {
  return (
    <div className="empty">
      <Icon name={icon} size={32} />
      <h2>{title}</h2>
      {children && <div className="muted">{children}</div>}
    </div>
  )
}

export function Spinner({ label = 'Loading…' }: { label?: string }) {
  return (
    <div className="loading" role="status">
      <span className="spinner" aria-hidden="true" />
      {label}
    </div>
  )
}

/** Loading / unavailable states for a cached API read. */
export function DataState({ loading, error }: { loading: boolean; error: unknown }) {
  if (loading) return <Spinner />
  return (
    <Empty icon={navigator.onLine ? 'close' : 'offline'} title="Not available">
      {navigator.onLine
        ? error instanceof Error
          ? error.message
          : 'This could not be loaded.'
        : "This hasn't been saved for offline use yet. Connect once to sync it."}
    </Empty>
  )
}

export function NoteLink({
  model,
  appLabel,
  id,
  count = 0,
}: {
  model: string
  appLabel: string
  id: number
  count?: number
}) {
  return (
    <Link
      className="note-link"
      to={`/notes/${appLabel}/${model}/${id}`}
      aria-label={count ? `${count} notes` : 'Add a note'}
      title="Notes"
    >
      <Icon name="note" size={18} />
      {count > 0 && <span className="badge">{count}</span>}
    </Link>
  )
}

export function Chip({ children, tone }: { children: ReactNode; tone?: 'success' | 'warning' | 'accent' }) {
  return <span className={`chip${tone ? ` chip-${tone}` : ''}`}>{children}</span>
}
