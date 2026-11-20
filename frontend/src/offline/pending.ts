// State of a not-yet-synced progress change: "saving" until a sync attempt that
// included it fails, then "unsynced" (saved on this device, waiting for the
// server); "saving" again while a retry runs. The UI only shows "unsynced".
import { useSyncExternalStore } from 'react'
import { getOutbox, subscribeOutbox } from './progress'
import { getSyncStatus, subscribeSyncStatus } from './sync'

export type PendingState = 'saving' | 'unsynced'

let cache: { outbox: unknown; status: unknown; map: Map<number, PendingState> } | null = null

function getPendingMap(): Map<number, PendingState> {
  const outbox = getOutbox()
  const status = getSyncStatus()
  if (cache?.outbox === outbox && cache.status === status) return cache.map
  const map = new Map<number, PendingState>()
  for (const op of outbox) {
    if (op.type !== 'completion') continue
    const attempted = status.unsentBefore !== null && Date.parse(op.at) <= status.unsentBefore
    map.set(op.topicId, status.phase !== 'syncing' && attempted ? 'unsynced' : 'saving')
  }
  cache = { outbox, status, map }
  return map
}

function subscribe(listener: () => void) {
  const offOutbox = subscribeOutbox(listener)
  const offStatus = subscribeSyncStatus(listener)
  return () => {
    offOutbox()
    offStatus()
  }
}

/** Display state of a topic's pending change (undefined when none). */
export function usePendingState(topicId: number): PendingState | undefined {
  return useSyncExternalStore(subscribe, () => getPendingMap().get(topicId))
}
