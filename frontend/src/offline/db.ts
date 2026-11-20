// IndexedDB schema. Everything here belongs to the signed-in user and is wiped
// on sign-out or when a different user signs in.
import { openDB, type DBSchema, type IDBPDatabase } from 'idb'

export interface CacheEntry<T = unknown> {
  /** API path, e.g. "/roadmaps/7". */
  key: string
  data: T
  fetchedAt: number
}

export type OutboxOp =
  | {
      id?: number
      type: 'enroll'
      roadmapId: number
      roadmapName: string
      at: string
    }
  | {
      id?: number
      type: 'completion'
      roadmapId: number
      topicId: number
      completed: boolean
      at: string
    }

export interface FileMeta {
  /** Absolute file URL (also the Cache Storage key). */
  url: string
  resourceId: number
  title: string
  size: number
  contentType: string
  savedAt: string
}

interface StudyplanDB extends DBSchema {
  cache: { key: string; value: CacheEntry }
  outbox: { key: number; value: OutboxOp }
  files: { key: string; value: FileMeta }
}

let dbPromise: Promise<IDBPDatabase<StudyplanDB>> | null = null

export function db() {
  dbPromise ??= openDB<StudyplanDB>('studyplan', 1, {
    upgrade(database) {
      database.createObjectStore('cache', { keyPath: 'key' })
      database.createObjectStore('outbox', { keyPath: 'id', autoIncrement: true })
      database.createObjectStore('files', { keyPath: 'url' })
    },
  })
  return dbPromise
}
