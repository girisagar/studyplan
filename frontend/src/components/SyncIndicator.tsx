import { timeAgo } from '../domain/format'
import { useOnline } from '../hooks/useOnline'
import { useOutbox } from '../offline/progress'
import { requestSync, useSyncStatus } from '../offline/sync'
import { Icon } from './Icon'

/** Header button: connection/sync state; click to sync now. */
export function SyncIndicator() {
  const status = useSyncStatus()
  const pending = useOutbox().length
  const online = useOnline()
  const syncing = status.phase === 'syncing'
  let label: string
  if (!online) label = pending ? `Offline · ${pending} change(s) waiting` : 'Offline'
  else if (syncing) label = 'Syncing…'
  else if (status.phase === 'signin') label = 'Sign in to sync'
  else if (status.phase === 'error') label = `Sync failed: ${status.error}`
  else if (pending) label = `${pending} change(s) waiting to sync`
  else label = status.lastSyncedAt ? `Synced ${timeAgo(status.lastSyncedAt)}` : 'Not synced yet'
  return (
    <button
      className={`sync-btn${!online ? ' is-offline' : ''}${status.phase === 'error' ? ' is-error' : ''}`}
      onClick={() => void requestSync(true)}
      disabled={!online || syncing}
      title={label}
      aria-label={label}
    >
      <Icon name={online ? 'sync' : 'offline'} size={18} className={syncing ? 'spin' : ''} />
      {pending > 0 && <span className="badge">{pending}</span>}
    </button>
  )
}
