// Files the user downloads for offline use (PDFs and other uploads under
// /media/). Bodies live in Cache Storage (FILES_CACHE), keyed by file URL, so the
// service worker can answer the same URL offline; metadata lives in IndexedDB.
import { useSyncExternalStore } from 'react'
import type { Resource } from '../api/types'
import { FILES_CACHE } from './constants'
import { db, type FileMeta } from './db'

let files = new Map<string, FileMeta>()
let progress = new Map<string, number>() // url -> 0..1 while downloading
const listeners = new Set<() => void>()

function emit() {
  listeners.forEach((listener) => listener())
}

function subscribe(listener: () => void) {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}

export async function hydrateFiles() {
  const metas = await (await db()).getAll('files')
  files = new Map(metas.map((m) => [m.url, m]))
  // The browser may evict Cache Storage under storage pressure: forget files
  // whose bodies are gone so the UI doesn't promise offline access.
  void (async () => {
    if (!('caches' in window)) return
    const cache = await caches.open(FILES_CACHE)
    const missing = []
    for (const url of files.keys()) if (!(await cache.match(url))) missing.push(url)
    if (missing.length) {
      const database = await db()
      for (const url of missing) {
        files.delete(url)
        await database.delete('files', url)
      }
      files = new Map(files)
      emit()
    }
  })()
}

export const getFiles = () => files
export const useFiles = () => useSyncExternalStore(subscribe, getFiles)
export const useDownloadProgress = () => useSyncExternalStore(subscribe, () => progress)

function setProgress(url: string, value: number | null) {
  progress = new Map(progress)
  if (value === null) progress.delete(url)
  else progress.set(url, value)
  emit()
}

/** Ask the browser not to evict offline data under storage pressure. */
async function persistStorage() {
  try {
    if (navigator.storage?.persist && !(await navigator.storage.persisted())) {
      await navigator.storage.persist()
    }
  } catch {
    // Not supported: data may be evicted, hydrateFiles() notices.
  }
}

/** Download a resource's file and keep it for offline use. */
export async function downloadFile(resource: Resource) {
  const url = resource.file_url
  if (!url || files.has(url) || progress.has(url)) return
  setProgress(url, 0)
  try {
    const response = await fetch(url, { cache: 'no-store' })
    if (!response.ok) throw new Error(`Download failed (${response.status}).`)
    const total = Number(response.headers.get('content-length')) || 0
    const contentType = response.headers.get('content-type') || 'application/octet-stream'
    const chunks: Uint8Array<ArrayBuffer>[] = []
    let received = 0
    const reader = response.body!.getReader()
    for (;;) {
      const { done, value } = await reader.read()
      if (done) break
      chunks.push(value)
      received += value.byteLength
      if (total) setProgress(url, received / total)
    }
    const blob = new Blob(chunks, { type: contentType })
    const cache = await caches.open(FILES_CACHE)
    await cache.put(
      url,
      new Response(blob, {
        headers: { 'Content-Type': contentType, 'Content-Length': String(blob.size) },
      }),
    )
    const meta: FileMeta = {
      url,
      resourceId: resource.id,
      title: resource.title,
      size: blob.size,
      contentType,
      savedAt: new Date().toISOString(),
    }
    await (await db()).put('files', meta)
    files = new Map(files).set(url, meta)
    void persistStorage()
  } finally {
    setProgress(url, null)
  }
}

/** Download several resources' files one after another. */
export async function downloadAll(resources: Resource[], onEach?: (done: number) => void) {
  let done = 0
  for (const resource of resources) {
    await downloadFile(resource)
    onEach?.(++done)
  }
}

export async function removeFile(url: string) {
  await (await caches.open(FILES_CACHE)).delete(url)
  await (await db()).delete('files', url)
  files = new Map(files)
  files.delete(url)
  emit()
}

export async function clearFiles() {
  await caches.delete(FILES_CACHE)
  await (await db()).clear('files')
  files = new Map()
  emit()
}

/** Distinct downloadable resources (with an uploaded file) in `resources`. */
export function downloadable(resources: Resource[]): Resource[] {
  const seen = new Set<string>()
  return resources.filter((r) => {
    if (!r.file_url || seen.has(r.file_url)) return false
    seen.add(r.file_url)
    return true
  })
}

export async function storageEstimate() {
  try {
    const [estimate, persisted] = await Promise.all([
      navigator.storage.estimate(),
      navigator.storage.persisted(),
    ])
    return { usage: estimate.usage ?? 0, quota: estimate.quota ?? 0, persisted }
  } catch {
    return null
  }
}
