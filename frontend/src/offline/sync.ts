// Sync engine: pushes the outbox (progress recorded offline) in order, then
// refreshes everything the app needs offline. Runs at startup, when the
// connection returns, when the app becomes visible, and after local changes.
import { useSyncExternalStore } from 'react'
import { api, ApiError, NetworkError, errorMessage } from '../api/client'
import type {
  CompletionRecord,
  Enrollment,
  ResourceListItem,
  RoadMapDetail,
  RoadMapListItem,
  User,
} from '../api/types'
import { getSession, subscribeSession, updateUser } from '../auth/session'
import { isOnline } from '../hooks/useOnline'
import { cacheKeys, deleteCacheKeys, fetchAndCache, patchCache } from './cache'
import type { OutboxOp } from './db'
import {
  COMPLETIONS_KEY,
  ENROLLMENTS_KEY,
  getOutbox,
  removeOp,
  setInflight,
  subscribeOutbox,
} from './progress'

export type SyncPhase = 'idle' | 'syncing' | 'offline' | 'error' | 'signin'

export interface SyncStatus {
  phase: SyncPhase
  /** Last complete refresh of offline data. */
  lastSyncedAt: number | null
  error: string | null
  /** Start time of the last sync attempt that left changes unsent (server
   * unreachable, error, or sign-in needed). Changes made before it are "not
   * synced"; newer ones are still waiting for their first attempt. */
  unsentBefore: number | null
}

const LAST_SYNC_KEY = 'studyplan.lastSync'
/** Refresh offline data at most this often unless asked (ms). */
const REFRESH_EVERY = 5 * 60_000

let status: SyncStatus = {
  phase: 'idle',
  lastSyncedAt: Number(localStorage.getItem(LAST_SYNC_KEY)) || null,
  error: null,
  unsentBefore: null,
}
const statusListeners = new Set<() => void>()
const noticeListeners = new Set<(message: string) => void>()

function setStatus(change: Partial<SyncStatus>) {
  status = { ...status, ...change }
  statusListeners.forEach((listener) => listener())
}

export const getSyncStatus = () => status

export function subscribeSyncStatus(listener: () => void) {
  statusListeners.add(listener)
  return () => {
    statusListeners.delete(listener)
  }
}

export function useSyncStatus() {
  return useSyncExternalStore(subscribeSyncStatus, getSyncStatus)
}

/** Messages for the user, e.g. a change the server refused. */
export function onSyncNotice(listener: (message: string) => void) {
  noticeListeners.add(listener)
  return () => {
    noticeListeners.delete(listener)
  }
}

function notice(message: string) {
  noticeListeners.forEach((listener) => listener(message))
}

let running: Promise<void> | null = null
let again: { full: boolean } | null = null

/** Push pending changes and refresh data (`full`: refresh even if recent). */
export function requestSync(full = false): Promise<void> {
  if (running) {
    again = { full: full || (again?.full ?? false) }
    return running
  }
  running = run(full).finally(() => {
    running = null
    const next = again
    again = null
    if (next) void requestSync(next.full)
  })
  return running
}

async function run(full: boolean) {
  const startedAt = Date.now()
  try {
    await attempt(full)
  } finally {
    // Whatever is still queued was due in this attempt and didn't get through.
    setStatus({ unsentBefore: getOutbox().length ? startedAt : null })
  }
}

async function attempt(full: boolean) {
  if (!isOnline()) {
    setStatus({ phase: 'offline' })
    return
  }
  const session = getSession()
  setStatus({ phase: 'syncing', error: null })
  try {
    if (session && !session.expired) await pushOutbox()
    const stale = !status.lastSyncedAt || Date.now() - status.lastSyncedAt > REFRESH_EVERY
    if (full || stale) {
      await pullAll()
      const now = Date.now()
      localStorage.setItem(LAST_SYNC_KEY, String(now))
      setStatus({ lastSyncedAt: now })
    }
    const expired = getSession()?.expired
    setStatus({ phase: expired && getOutbox().length ? 'signin' : 'idle' })
  } catch (error) {
    if (error instanceof NetworkError) setStatus({ phase: 'offline' })
    else if (error instanceof ApiError && error.status === 401) setStatus({ phase: 'signin' })
    else setStatus({ phase: 'error', error: errorMessage(error) })
  }
}

/** Server refused the change for good (not a transient failure). */
const isRejection = (error: unknown) =>
  error instanceof ApiError && [400, 403, 404, 409, 422].includes(error.status)

async function pushOutbox() {
  for (;;) {
    const op = getOutbox()[0]
    if (!op) return
    setInflight(op.id!)
    try {
      await send(op)
    } catch (error) {
      if (!isRejection(error)) throw error
      notice(rejectionMessage(op))
    } finally {
      setInflight(null)
    }
    await removeOp(op.id!)
  }
}

async function send(op: OutboxOp) {
  if (op.type === 'enroll') {
    const enrollment = await api<Enrollment>(`/progress/roadmaps/${op.roadmapId}/enrollment`, {
      method: 'PUT',
      body: { started_at: op.at },
    })
    await patchCache<Enrollment[]>(ENROLLMENTS_KEY, (list) => [
      ...list.filter((e) => e.roadmap_id !== enrollment.roadmap_id),
      enrollment,
    ])
    return
  }
  await api(`/progress/roadmaps/${op.roadmapId}/topics/${op.topicId}/completion`, {
    method: 'PUT',
    body: { completed: op.completed, completed_at: op.at },
  })
  // Mirror the server's new state until the next refresh.
  await patchCache<CompletionRecord[]>(COMPLETIONS_KEY, (list) => {
    const rest = list.filter((r) => r.topic_id !== op.topicId)
    return op.completed ? [...rest, { topic_id: op.topicId, completed_at: op.at }] : rest
  })
}

function rejectionMessage(op: OutboxOp) {
  return op.type === 'enroll'
    ? `Couldn't follow “${op.roadmapName}”; the change was discarded.`
    : 'A progress change was refused by the server (the topic may have moved) and was discarded.'
}

/** Run `tasks` with at most `limit` in flight; failures don't stop the rest. */
async function pool(tasks: (() => Promise<unknown>)[], limit = 4) {
  const queue = [...tasks]
  let firstError: unknown = null
  await Promise.all(
    Array.from({ length: Math.min(limit, queue.length) }, async () => {
      for (let task = queue.shift(); task; task = queue.shift()) {
        try {
          await task()
        } catch (error) {
          firstError ??= error
        }
      }
    }),
  )
  if (firstError instanceof NetworkError) throw firstError
}

/** Refresh the offline data set and drop cached entries that no longer exist. */
async function pullAll() {
  const session = getSession()
  const signedIn = Boolean(session && !session.expired)
  if (signedIn) {
    const [user] = await Promise.all([
      api<User>('/auth/me'),
      fetchAndCache(ENROLLMENTS_KEY),
      fetchAndCache(COMPLETIONS_KEY),
    ])
    updateUser(user)
  }
  const [roadmaps, resources] = await Promise.all([
    fetchAndCache<RoadMapListItem[]>('/roadmaps'),
    fetchAndCache<ResourceListItem[]>('/library/resources'),
    fetchAndCache('/library/kinds'),
  ])
  const details = await Promise.all(
    roadmaps.map((r) => fetchAndCache<RoadMapDetail>(`/roadmaps/${r.id}`)),
  )
  const courseIds = [...new Set(details.flatMap((d) => d.schedule.map((s) => s.course.id)))]
  const keep = new Set([
    ...roadmaps.map((r) => `/roadmaps/${r.id}`),
    ...courseIds.map((id) => `/curriculum/courses/${id}`),
    ...resources.map((r) => `/library/resources/${r.id}`),
  ])
  await pool([
    ...courseIds.map((id) => () => fetchAndCache(`/curriculum/courses/${id}`)),
    ...resources.map((r) => () => fetchAndCache(`/library/resources/${r.id}`)),
  ])
  const prunable = /^\/(roadmaps\/\d+|curriculum\/courses\/\d+|library\/resources\/\d+)$/
  await deleteCacheKeys(cacheKeys().filter((key) => prunable.test(key) && !keep.has(key)))
}

/** Forget sync history (after local data was wiped). */
export function resetSyncState() {
  localStorage.removeItem(LAST_SYNC_KEY)
  setStatus({ phase: 'idle', lastSyncedAt: null, error: null, unsentBefore: null })
}

let started = false

export function startSync() {
  if (started) return
  started = true
  void requestSync(true)
  window.addEventListener('online', () => void requestSync(true))
  window.addEventListener('offline', () => setStatus({ phase: 'offline' }))
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') void requestSync()
  })
  // Local changes: push soon (batching rapid taps).
  let timer: number | undefined
  subscribeOutbox(() => {
    window.clearTimeout(timer)
    if (getOutbox().length) timer = window.setTimeout(() => void requestSync(), 800)
  })
  // Retry pending changes while the app is open (e.g. after a server error).
  window.setInterval(() => {
    if (getOutbox().length && isOnline()) void requestSync()
  }, 60_000)
  // Signing in (or a refreshed session) may unblock pending changes.
  let lastUser = getSession()?.user.id
  let lastExpired = getSession()?.expired
  subscribeSession(() => {
    const session = getSession()
    if (session?.user.id !== lastUser || session?.expired !== lastExpired) {
      lastUser = session?.user.id
      lastExpired = session?.expired
      if (session && !session.expired) void requestSync(true)
    }
  })
}
