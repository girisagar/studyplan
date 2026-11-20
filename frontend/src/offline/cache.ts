// API response cache: IndexedDB for persistence, mirrored in memory so screens
// render synchronously (also offline). Keys are API paths. The whole cache is
// loaded at startup (hydrateCache); it is small (a few hundred KB of JSON).
import { useCallback, useEffect, useSyncExternalStore } from 'react'
import { api } from '../api/client'
import { isOnline, useOnline } from '../hooks/useOnline'
import { db, type CacheEntry } from './db'

interface FetchStatus {
  fetching: boolean
  error: unknown
}

const IDLE: FetchStatus = { fetching: false, error: null }
const memory = new Map<string, CacheEntry>()
const statuses = new Map<string, FetchStatus>()
const listeners = new Map<string, Set<() => void>>()
const inflight = new Map<string, Promise<unknown>>()
const anyListeners = new Set<() => void>()
let version = 0

function notify(key: string) {
  version++
  listeners.get(key)?.forEach((listener) => listener())
  anyListeners.forEach((listener) => listener())
}

function subscribeAny(listener: () => void) {
  anyListeners.add(listener)
  return () => {
    anyListeners.delete(listener)
  }
}

/** Changes whenever any cached entry changes (for views over many keys). */
export function useCacheVersion() {
  return useSyncExternalStore(subscribeAny, () => version)
}

export const cacheKeys = () => [...memory.keys()]

export async function deleteCacheKeys(keys: string[]) {
  if (!keys.length) return
  const database = await db()
  for (const key of keys) {
    memory.delete(key)
    notify(key)
    await database.delete('cache', key)
  }
}

export async function hydrateCache() {
  const entries = await (await db()).getAll('cache')
  for (const entry of entries) memory.set(entry.key, entry)
}

export function readCache<T>(key: string): CacheEntry<T> | undefined {
  return memory.get(key) as CacheEntry<T> | undefined
}

export async function writeCache<T>(key: string, data: T) {
  const entry: CacheEntry<T> = { key, data, fetchedAt: Date.now() }
  memory.set(key, entry)
  notify(key)
  await (await db()).put('cache', entry)
}

/** Change cached data in place (keeps fetchedAt). No-op if the key is absent. */
export async function patchCache<T>(key: string, change: (data: T) => T) {
  const entry = readCache<T>(key)
  if (!entry) return
  const next = { ...entry, data: change(entry.data) }
  memory.set(key, next)
  notify(key)
  await (await db()).put('cache', next)
}

export async function clearCache() {
  const keys = [...memory.keys()]
  memory.clear()
  keys.forEach(notify)
  await (await db()).clear('cache')
}

function setStatus(key: string, status: FetchStatus) {
  statuses.set(key, status)
  notify(key)
}

/** GET `path` and cache the response; concurrent calls share one request. */
export function fetchAndCache<T>(path: string): Promise<T> {
  let request = inflight.get(path) as Promise<T> | undefined
  if (!request) {
    setStatus(path, { fetching: true, error: statuses.get(path)?.error ?? null })
    request = api<T>(path)
      .then(async (data) => {
        await writeCache(path, data)
        setStatus(path, IDLE)
        return data
      })
      .catch((error: unknown) => {
        setStatus(path, { fetching: false, error })
        throw error
      })
      .finally(() => inflight.delete(path))
    inflight.set(path, request)
  }
  return request
}

function subscribeKey(key: string, listener: () => void) {
  let set = listeners.get(key)
  if (!set) listeners.set(key, (set = new Set()))
  set.add(listener)
  return () => {
    set.delete(listener)
  }
}

/** The cached entry for `key` (undefined if absent); re-renders on change. */
export function useCached<T>(key: string | null): CacheEntry<T> | undefined {
  return useSyncExternalStore(
    useCallback((listener: () => void) => (key ? subscribeKey(key, listener) : () => {}), [key]),
    () => (key ? readCache<T>(key) : undefined),
  )
}

function useFetchStatus(key: string | null): FetchStatus {
  return useSyncExternalStore(
    useCallback((listener: () => void) => (key ? subscribeKey(key, listener) : () => {}), [key]),
    () => (key ? (statuses.get(key) ?? IDLE) : IDLE),
  )
}

export interface ApiState<T> {
  data: T | undefined
  fetchedAt: number | undefined
  /** Loading with nothing cached yet. */
  loading: boolean
  /** Last fetch failed; `data` may still hold an older cached copy. */
  error: unknown
  refresh: () => Promise<void>
}

/**
 * Stale-while-revalidate read of an API path: returns the cached copy at once
 * and refetches in the background when online and older than `maxAge` ms.
 */
export function useApi<T>(path: string | null, maxAge = 60_000): ApiState<T> {
  const entry = useCached<T>(path)
  const status = useFetchStatus(path)
  const online = useOnline()

  const refresh = useCallback(async () => {
    if (path) await fetchAndCache<T>(path).catch(() => {})
  }, [path])

  useEffect(() => {
    if (!path || !isOnline()) return
    const cached = readCache(path)
    if (!cached || Date.now() - cached.fetchedAt > maxAge) void refresh()
  }, [path, online, maxAge, refresh])

  return {
    data: entry?.data,
    fetchedAt: entry?.fetchedAt,
    loading: !entry && (status.fetching || (online && !status.error)),
    error: status.error,
    refresh,
  }
}
