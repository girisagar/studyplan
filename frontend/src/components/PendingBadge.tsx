import { usePendingState } from '../offline/pending'
import { Icon } from './Icon'

/** "Not synced" for a topic's progress change, shown only once a sync attempt
 * found the server unreachable (offline, network/server error, sign-in needed).
 * Nothing while the change is on its way or after it synced. */
export function PendingBadge({ topicId, long = false }: { topicId: number; long?: boolean }) {
  if (usePendingState(topicId) !== 'unsynced') return null
  return (
    <span className="pending" title="Saved on this device; it will sync when the server can be reached">
      <Icon name="cloud" size={long ? 14 : 12} /> {long ? 'Not synced yet' : 'not synced'}
    </span>
  )
}
