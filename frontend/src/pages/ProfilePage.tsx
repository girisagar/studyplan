import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { logout } from '../auth/actions'
import { useSession } from '../auth/session'
import { Icon } from '../components/Icon'
import { toast } from '../components/toast'
import { Page } from '../components/ui'
import { formatBytes, formatDate, timeAgo } from '../domain/format'
import { useInstall } from '../hooks/useInstall'
import { useOnline } from '../hooks/useOnline'
import { removeFile, storageEstimate, useFiles } from '../offline/files'
import { useOutbox } from '../offline/progress'
import { requestSync, useSyncStatus } from '../offline/sync'

type Theme = 'light' | 'dark' | 'system'
const THEME_KEY = 'studyplan.theme'

function applyTheme(theme: Theme) {
  const resolved =
    theme === 'system' ? (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light') : theme
  document.documentElement.dataset.theme = resolved
}

export function ProfilePage() {
  const session = useSession()
  const navigate = useNavigate()
  const online = useOnline()
  const status = useSyncStatus()
  const outbox = useOutbox()
  const files = useFiles()
  const install = useInstall()
  const [theme, setTheme] = useState<Theme>(() => (localStorage.getItem(THEME_KEY) as Theme) || 'system')
  const [storage, setStorage] = useState<Awaited<ReturnType<typeof storageEstimate>>>(null)

  useEffect(() => {
    void storageEstimate().then(setStorage)
  }, [files])

  const fileList = [...files.values()].sort((a, b) => a.title.localeCompare(b.title))
  const totalSize = fileList.reduce((sum, f) => sum + f.size, 0)

  async function signOut() {
    const warning = outbox.length
      ? `${outbox.length} progress change(s) haven't synced yet and will be lost. Sign out anyway?`
      : 'Sign out? Offline data and downloaded files on this device will be removed.'
    if (!confirm(warning)) return
    await logout()
    toast('Signed out.')
    navigate('/')
  }

  return (
    <Page title="Profile">
      <section className="card">
        <h2>Account</h2>
        {session ? (
          <>
            <p>
              <strong>{session.user.username}</strong>
              {session.user.email && <span className="muted"> · {session.user.email}</span>}
            </p>
            <p className="muted small">Member since {formatDate(session.user.date_joined)}</p>
            <button className="btn" onClick={signOut}>
              <Icon name="logout" size={16} /> Sign out
            </button>
          </>
        ) : (
          <div className="row gap">
            <Link className="btn btn-primary" to="/login">
              Sign in
            </Link>
            <Link className="btn" to="/register">
              Create account
            </Link>
          </div>
        )}
      </section>

      <section className="card">
        <h2>Sync</h2>
        <p>
          {online ? 'Online' : 'Offline'} ·{' '}
          {status.lastSyncedAt ? `last synced ${timeAgo(status.lastSyncedAt)}` : 'not synced yet'}
        </p>
        {outbox.length > 0 ? (
          <p className="muted small">
            {outbox.length} change(s) recorded on this device will be sent when you're online.
          </p>
        ) : (
          <p className="muted small">All progress is saved to your account.</p>
        )}
        {status.phase === 'error' && <p className="form-error">{status.error}</p>}
        {status.phase === 'signin' && (
          <p className="form-note">
            <Link to="/login">Sign in again</Link> to sync your changes.
          </p>
        )}
        <button className="btn" disabled={!online || status.phase === 'syncing'} onClick={() => void requestSync(true)}>
          <Icon name="sync" size={16} className={status.phase === 'syncing' ? 'spin' : ''} />
          {status.phase === 'syncing' ? 'Syncing…' : 'Sync now'}
        </button>
      </section>

      <section className="card">
        <h2>Offline files</h2>
        <p className="muted small">
          {fileList.length
            ? `${fileList.length} file(s), ${formatBytes(totalSize)}.`
            : 'No files downloaded. Use the download button on a resource to keep it offline.'}
          {storage &&
            ` Device storage used by this app: ${formatBytes(storage.usage)} of ${formatBytes(storage.quota)}.` +
              (storage.persisted ? ' Storage is persistent.' : ' The browser may clear it if space runs low.')}
        </p>
        {fileList.length > 0 && (
          <ul className="plain-list">
            {fileList.map((f) => (
              <li key={f.url} className="row between">
                <Link to={`/library/${f.resourceId}`}>{f.title}</Link>
                <span className="row gap-sm">
                  <span className="muted small">{formatBytes(f.size)}</span>
                  <button className="icon-btn" aria-label={`Remove ${f.title}`} onClick={() => void removeFile(f.url)}>
                    <Icon name="trash" size={16} />
                  </button>
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="card">
        <h2>Appearance</h2>
        <div className="segmented" role="radiogroup" aria-label="Theme">
          {(['light', 'dark', 'system'] as Theme[]).map((t) => (
            <button
              key={t}
              role="radio"
              aria-checked={theme === t}
              className={theme === t ? 'active' : ''}
              onClick={() => {
                setTheme(t)
                localStorage.setItem(THEME_KEY, t)
                applyTheme(t)
              }}
            >
              {t[0].toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>
      </section>

      <section className="card">
        <h2>App</h2>
        {install.installed ? (
          <p className="muted small">Installed on this device.</p>
        ) : install.canPrompt ? (
          <button className="btn btn-primary" onClick={() => void install.prompt()}>
            <Icon name="install" size={16} /> Install app
          </button>
        ) : install.ios ? (
          <p className="muted small">
            To install on iPhone or iPad: tap Share, then “Add to Home Screen”.
          </p>
        ) : (
          <p className="muted small">Use your browser's menu to install this app.</p>
        )}
      </section>
    </Page>
  )
}

// Follow system theme changes while "system" is selected.
matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
  if ((localStorage.getItem(THEME_KEY) || 'system') === 'system') applyTheme('system')
})
