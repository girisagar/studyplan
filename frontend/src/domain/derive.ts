// Views derived on the client from cached server data plus local progress, so
// screens stay correct offline and react instantly to checked topics. Ordering
// and week placement come from the server's outline (RoadMapDetail.sections);
// only completion is recomputed here.
import type {
  CourseRef,
  CourseState,
  Enrollment,
  Finish,
  OutlineChapter,
  OutlineTopic,
  Progress,
  RoadMapDetail,
  ScheduledCourse,
} from '../api/types'
import type { LocalProgress } from '../offline/progress'

export interface ItemView {
  number: number
  week: number
  course: CourseRef
  chapter: OutlineChapter
  topic: OutlineTopic
  completed: boolean
  /** Change not synced yet. */
  pending: boolean
}

export interface GroupView {
  course: CourseRef
  chapter: OutlineChapter
  items: ItemView[]
  completed: number
  hours: number
  percent: number
}

export interface SectionView {
  week: number
  title: string
  total: number
  completed: number
  hours: number
  percent: number
  courses: CourseRef[]
  groups: GroupView[]
}

export interface CourseView extends Omit<ScheduledCourse, 'progress' | 'state'> {
  progress: Progress
  state: CourseState
}

export interface RoadmapView {
  roadmap: RoadMapDetail
  sections: SectionView[]
  items: ItemView[]
  schedule: CourseView[]
  progress: Progress
  finish: Finish
  next: ItemView | null
  following: boolean
}

export const percent = (completed: number, total: number) =>
  total ? Math.round((100 * completed) / total) : 0

export const progressOf = (items: ItemView[]): Progress => {
  const completed = items.filter((i) => i.completed).length
  return { completed, total: items.length, percent: percent(completed, items.length) }
}

function groupView(course: CourseRef, chapter: OutlineChapter, items: ItemView[]): GroupView {
  const completed = items.filter((i) => i.completed).length
  return {
    course,
    chapter,
    items,
    completed,
    hours: items.reduce((sum, i) => sum + i.topic.total_time, 0),
    percent: percent(completed, items.length),
  }
}

function sectionView(base: { week: number }, groups: GroupView[]): SectionView {
  const total = groups.reduce((sum, g) => sum + g.items.length, 0)
  const completed = groups.reduce((sum, g) => sum + g.completed, 0)
  return {
    week: base.week,
    title: groups.map((g) => g.chapter.name).join(' · '),
    total,
    completed,
    hours: groups.reduce((sum, g) => sum + g.hours, 0),
    percent: percent(completed, total),
    courses: [...new Map(groups.map((g) => [g.course.id, g.course])).values()],
    groups,
  }
}

export function buildRoadmapView(roadmap: RoadMapDetail, local: LocalProgress): RoadmapView {
  const items: ItemView[] = []
  const sections = roadmap.sections.map((section) =>
    sectionView(
      section,
      section.groups.map((group) =>
        groupView(
          group.course,
          group.chapter,
          group.items.map((item) => {
            const view: ItemView = {
              number: item.number,
              week: item.week,
              course: item.course,
              chapter: item.chapter,
              topic: item.topic,
              completed: local.done.has(item.topic.id),
              pending: local.pendingTopics.has(item.topic.id),
            }
            items.push(view)
            return view
          }),
        ),
      ),
    ),
  )
  const schedule: CourseView[] = roadmap.schedule.map((link) => {
    const progress = progressOf(items.filter((i) => i.course.id === link.course.id))
    const done = progress.total > 0 && progress.completed === progress.total
    return { ...link, progress, state: done ? 'done' : 'upcoming' }
  })
  const current = schedule.find((c) => c.state !== 'done')
  if (current) current.state = 'current'
  const progress = progressOf(items)
  const finish: Finish =
    progress.total && progress.completed === progress.total
      ? 'complete'
      : progress.completed
        ? 'progress'
        : 'todo'
  return {
    roadmap,
    sections,
    items,
    schedule,
    progress,
    finish,
    next: items.find((i) => !i.completed) ?? null,
    following: local.isFollowing(roadmap.id),
  }
}

/** The roadmap outline restricted to one course (weeks stay on the roadmap timeline). */
export function courseSections(view: RoadmapView, courseId: number): SectionView[] {
  return view.sections
    .map((s) => sectionView(s, s.groups.filter((g) => g.course.id === courseId)))
    .filter((s) => s.groups.length > 0)
}

/** Which topic the player opens: the requested one, else the first unfinished
 * one (in `week` if given), else the first. */
export function pickItem(items: ItemView[], topicId: number | null, week: number | null) {
  if (topicId !== null) return items.find((i) => i.topic.id === topicId) ?? null
  const pool = week !== null ? items.filter((i) => i.week === week) : items
  return pool.find((i) => !i.completed) ?? pool[0] ?? null
}

export type Pace = 'ahead' | 'on_track' | 'behind' | 'done'

export interface Snapshot {
  view: RoadmapView
  enrollment: Enrollment
  currentSection: SectionView | null
  /** Week the schedule expects by now (from when the user started). */
  scheduledWeek: number | null
  pace: Pace | null
  hoursTotal: number
  hoursDone: number
  lastActivity: string
}

export function localDate(value: string | Date) {
  const d = new Date(value)
  return new Date(d.getFullYear(), d.getMonth(), d.getDate())
}

export function snapshot(view: RoadmapView, enrollment: Enrollment, local: LocalProgress): Snapshot {
  const weeks = view.roadmap.total_weeks
  const next = view.next
  let scheduledWeek: number | null = null
  let pace: Pace | null = null
  if (weeks) {
    const days = Math.floor(
      (localDate(new Date()).getTime() - localDate(enrollment.started_at).getTime()) / 86_400_000,
    )
    scheduledWeek = Math.min(weeks, Math.max(1, Math.floor(days / 7) + 1))
    pace = !next
      ? 'done'
      : next.week > scheduledWeek
        ? 'ahead'
        : next.week < scheduledWeek
          ? 'behind'
          : 'on_track'
  }
  const times = view.items.map((i) => local.done.get(i.topic.id)).filter((t): t is string => !!t)
  return {
    view,
    enrollment,
    currentSection: next ? (view.sections.find((s) => s.week === next.week) ?? null) : null,
    scheduledWeek,
    pace,
    hoursTotal: view.items.reduce((sum, i) => sum + i.topic.total_time, 0),
    hoursDone: view.items.reduce((sum, i) => sum + (i.completed ? i.topic.total_time : 0), 0),
    lastActivity: times.reduce((a, b) => (a > b ? a : b), enrollment.started_at),
  }
}

/** Monday 00:00 (local time) of the week containing `date`. */
export function weekStart(date = new Date()) {
  const day = localDate(date)
  day.setDate(day.getDate() - ((day.getDay() + 6) % 7))
  return day
}

export interface StudyStats {
  completed: number
  thisWeek: number
  /** Estimated hours of completed topics. */
  hoursDone: number
}

/** Stats over every completed topic (each counted once). `hours` maps topic id
 * to estimated hours for the topics known locally. */
export function studyStats(local: LocalProgress, hours: Map<number, number>): StudyStats {
  const monday = weekStart().getTime()
  let thisWeek = 0
  let hoursDone = 0
  for (const [topicId, at] of local.done) {
    if (new Date(at).getTime() >= monday) thisWeek++
    hoursDone += hours.get(topicId) ?? 0
  }
  return { completed: local.done.size, thisWeek, hoursDone }
}

/** Completions per week for the last `weeks` weeks, oldest first. */
export function weeklyCounts(local: LocalProgress, weeks = 8) {
  const first = weekStart()
  first.setDate(first.getDate() - 7 * (weeks - 1))
  const result = Array.from({ length: weeks }, (_, i) => {
    const start = new Date(first)
    start.setDate(first.getDate() + 7 * i)
    return { start, count: 0 }
  })
  for (const at of local.done.values()) {
    const index = Math.floor((weekStart(new Date(at)).getTime() - first.getTime()) / (7 * 86_400_000))
    if (index >= 0 && index < weeks) result[index].count++
  }
  return result
}
