import { useMemo } from 'react'
import type { CourseDetail, RoadMapDetail, RoadMapListItem } from '../api/types'
import {
  buildRoadmapView,
  snapshot,
  studyStats,
  type RoadmapView,
  type Snapshot,
} from '../domain/derive'
import { readCache, useApi, useCacheVersion } from '../offline/cache'
import { useLocalProgress } from '../offline/progress'

export function useRoadmapView(id: number) {
  const state = useApi<RoadMapDetail>(`/roadmaps/${id}`)
  const local = useLocalProgress()
  const view = useMemo(
    () => (state.data ? buildRoadmapView(state.data, local) : undefined),
    [state.data, local],
  )
  return { ...state, view, local }
}

export function useCourse(id: number) {
  return useApi<CourseDetail>(`/curriculum/courses/${id}`)
}

/** Views of every roadmap cached locally (refreshed by the sync engine). */
export function useAllRoadmapViews(): RoadmapView[] {
  const version = useCacheVersion()
  const local = useLocalProgress()
  return useMemo(() => {
    void version
    const list = readCache<RoadMapListItem[]>('/roadmaps')?.data ?? []
    return list
      .map((r) => readCache<RoadMapDetail>(`/roadmaps/${r.id}`)?.data)
      .filter((d): d is RoadMapDetail => !!d)
      .map((d) => buildRoadmapView(d, local))
  }, [version, local])
}

/** The user's followed roadmaps, most recently active first, plus stats. */
export function useLearning() {
  const views = useAllRoadmapViews()
  const local = useLocalProgress()
  return useMemo(() => {
    const byId = new Map(views.map((v) => [v.roadmap.id, v]))
    const snapshots: Snapshot[] = local.enrollments
      .map((e) => {
        const view = byId.get(e.roadmap_id)
        return view ? snapshot(view, e, local) : null
      })
      .filter((s): s is Snapshot => !!s)
      .sort((a, b) => b.lastActivity.localeCompare(a.lastActivity))
    const hours = new Map<number, number>()
    const topics = new Map<number, { view: RoadmapView; item: RoadmapView['items'][number] }>()
    for (const view of views) {
      for (const item of view.items) {
        hours.set(item.topic.id, item.topic.total_time)
        // Prefer a followed roadmap when a topic appears in several.
        if (!topics.has(item.topic.id) || view.following) topics.set(item.topic.id, { view, item })
      }
    }
    return { views, snapshots, stats: studyStats(local, hours), topics, local }
  }, [views, local])
}
