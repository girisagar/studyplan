// The user's progress as the app shows it: the server's completions and
// enrollments (cached API responses) with the not-yet-synced changes in the
// outbox applied on top. Changes made offline are recorded in the outbox with
// the time they happened and pushed by the sync engine (sync.ts).
import { useMemo, useSyncExternalStore } from 'react'
import type { CompletionRecord, Enrollment } from '../api/types'
import { readCache, useCached } from './cache'
import { db, type OutboxOp } from './db'

export const COMPLETIONS_KEY = '/progress/completions'
export const ENROLLMENTS_KEY = '/progress/enrollments'

let outbox: OutboxOp[] = []
let inflightId: number | null = null
const listeners = new Set<() => void>()

function emit() {
  outbox = [...outbox]
  listeners.forEach((listener) => listener())
}

export async function hydrateOutbox() {
  outbox = await (await db()).getAll('outbox')
}

export function subscribeOutbox(listener: () => void) {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}

export const getOutbox = () => outbox
export const useOutbox = () => useSyncExternalStore(subscribeOutbox, getOutbox)

/** The op the sync engine is sending (it must not be cancelled meanwhile). */
export function setInflight(id: number | null) {
  inflightId = id
}

async function addOp(op: OutboxOp) {
  const id = await (await db()).add('outbox', op)
  outbox.push({ ...op, id })
  emit()
}

export async function removeOp(id: number) {
  await (await db()).delete('outbox', id)
  outbox = outbox.filter((op) => op.id !== id)
  emit()
}

export async function clearOutbox() {
  await (await db()).clear('outbox')
  outbox = []
  emit()
}

function serverDone(): Set<number> {
  const records = readCache<CompletionRecord[]>(COMPLETIONS_KEY)?.data ?? []
  return new Set(records.map((r) => r.topic_id))
}

function serverEnrollments(): Enrollment[] {
  return readCache<Enrollment[]>(ENROLLMENTS_KEY)?.data ?? []
}

/** Record that a topic is (not) completed; synced when online. */
export async function setTopicCompleted(roadmapId: number, topicId: number, completed: boolean) {
  const ops = outbox.filter(
    (op): op is Extract<OutboxOp, { type: 'completion' }> =>
      op.type === 'completion' && op.topicId === topicId,
  )
  const sending = ops.find((op) => op.id === inflightId)
  const queued = ops.filter((op) => op.id !== inflightId)
  // State the server will have once anything already in flight lands.
  const base = sending ? sending.completed : serverDone().has(topicId)
  for (const op of queued) await removeOp(op.id!)
  if (completed !== base) {
    await addOp({ type: 'completion', roadmapId, topicId, completed, at: new Date().toISOString() })
  }
}

/** Follow a roadmap (needed before recording progress in it). */
export async function followRoadmap(roadmapId: number, roadmapName: string) {
  const following =
    serverEnrollments().some((e) => e.roadmap_id === roadmapId) ||
    outbox.some((op) => op.type === 'enroll' && op.roadmapId === roadmapId)
  if (!following) {
    await addOp({ type: 'enroll', roadmapId, roadmapName, at: new Date().toISOString() })
  }
}

export interface LocalProgress {
  /** Completed topic id -> completion time (ISO). */
  done: Map<number, string>
  /** Topics with changes waiting to sync. */
  pendingTopics: Set<number>
  enrollments: Enrollment[]
  /** Roadmaps followed locally but not synced yet. */
  pendingRoadmaps: Set<number>
  isFollowing: (roadmapId: number) => boolean
  pendingCount: number
  /** The user's enrollments have been fetched at least once (so "not
   * following" is real, not just unknown). */
  known: boolean
}

export function computeLocalProgress(
  records: CompletionRecord[],
  serverEnrolled: Enrollment[] | undefined,
  ops: OutboxOp[],
): LocalProgress {
  const known = serverEnrolled !== undefined
  const done = new Map(records.map((r) => [r.topic_id, r.completed_at]))
  const pendingTopics = new Set<number>()
  const enrollments = [...(serverEnrolled ?? [])]
  const pendingRoadmaps = new Set<number>()
  for (const op of ops) {
    if (op.type === 'completion') {
      pendingTopics.add(op.topicId)
      if (op.completed) {
        if (!done.has(op.topicId)) done.set(op.topicId, op.at)
      } else done.delete(op.topicId)
    } else if (!enrollments.some((e) => e.roadmap_id === op.roadmapId)) {
      enrollments.push({ roadmap_id: op.roadmapId, roadmap_name: op.roadmapName, started_at: op.at })
      pendingRoadmaps.add(op.roadmapId)
    }
  }
  const followed = new Set(enrollments.map((e) => e.roadmap_id))
  return {
    done,
    pendingTopics,
    enrollments,
    pendingRoadmaps,
    isFollowing: (id) => followed.has(id),
    pendingCount: ops.length,
    known,
  }
}

export function useLocalProgress(): LocalProgress {
  const completions = useCached<CompletionRecord[]>(COMPLETIONS_KEY)
  const enrollments = useCached<Enrollment[]>(ENROLLMENTS_KEY)
  const ops = useOutbox()
  return useMemo(
    () => computeLocalProgress(completions?.data ?? [], enrollments?.data, ops),
    [completions, enrollments, ops],
  )
}
