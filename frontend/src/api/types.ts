// Response/request shapes of the Django API (backend/*/schemas.py).
// Weeks are on the roadmap timeline unless noted; `total_time`/`hours` are
// estimated hours. Rich-text fields (`description`, note `body`) are HTML
// sanitized by the server.

export interface Progress {
  completed: number
  total: number
  percent: number
}

export interface User {
  id: number
  username: string
  email: string
  is_staff: boolean
  date_joined: string
  can_edit_topics: boolean
}

export interface TokenPair {
  access: string
  refresh: string
}

export interface SessionResponse extends TokenPair {
  user: User
}

export interface NamedRef {
  id: number
  name: string
}

export type ResourceKind =
  | 'book'
  | 'paper'
  | 'problem_set'
  | 'solutions'
  | 'notes'
  | 'code'
  | 'slides'
  | 'video'
  | 'other'

export interface Resource {
  id: number
  title: string
  author: string
  kind: ResourceKind
  kind_label: string
  url: string
  /** Where to open it: the uploaded file if any, else `url`. */
  href: string | null
  /** Absolute URL of the uploaded file (downloadable for offline use). */
  file_url: string | null
  thumbnail_url: string | null
  is_pdf: boolean
}

export interface ResourceListItem extends Resource {
  roadmaps: NamedRef[]
}

export interface ResourceDetail {
  resource: Resource
  note_count: number
  placements: { roadmap: NamedRef; course: NamedRef; start_week: number }[]
  courses: NamedRef[]
  chapters: { id: number; name: string; course: NamedRef; roadmap: NamedRef; week: number }[]
  topics: {
    id: number
    topic_name: string
    chapter: NamedRef
    course: NamedRef
    roadmap: NamedRef
    week: number
  }[]
}

export interface Kind {
  value: ResourceKind
  label: string
}

export interface Tag {
  id: number
  name: string
}

export interface CourseRef {
  id: number
  name: string
}

/** `week` is the week within the chapter's course. */
export interface ChapterRef {
  id: number
  name: string
  week: number
  order: number
}

export interface TopicBrief {
  id: number
  topic_name: string
  total_time: number
  order: number
  tags: Tag[]
}

export interface TopicOut extends TopicBrief {
  description: string
  resources: Resource[]
  note_count: number
}

export interface ChapterOut extends ChapterRef {
  description: string
  deliverable: string
  resources: Resource[]
  note_count: number
}

export interface ChapterWithTopics extends ChapterOut {
  topics: TopicOut[]
}

export interface CourseOut extends CourseRef {
  description: string
  resources: Resource[]
  note_count: number
}

export interface CourseDetail extends CourseOut {
  chapters: ChapterWithTopics[]
}

export interface RoadMapRef {
  id: number
  name: string
}

export interface RoadMapOut extends RoadMapRef {
  description: string
  note_count: number
}

export interface OutlineTopic extends TopicBrief {
  note_count: number
}

export interface OutlineChapter extends ChapterRef {
  note_count: number
  position: number | null
}

export interface OutlineItem {
  number: number
  week: number
  completed: boolean
  course: CourseRef
  chapter: OutlineChapter
  topic: OutlineTopic
}

export interface OutlineGroup {
  course: CourseRef
  chapter: OutlineChapter
  items: OutlineItem[]
  completed: number
  hours: number
  percent: number
}

export interface OutlineSection {
  week: number
  title: string
  total: number
  completed: number
  hours: number
  percent: number
  courses: CourseRef[]
  groups: OutlineGroup[]
}

export type CourseState = 'done' | 'current' | 'upcoming'

export interface ScheduledCourseBrief {
  course: CourseRef
  start_week: number
  order: number
  first_week: number
  last_week: number
  weeks: number
  topic_count: number
  hours: number
  progress: Progress | null
  state: CourseState | null
}

export interface ScheduledCourse extends ScheduledCourseBrief {
  course: CourseOut
}

export interface RoadMapListItem extends RoadMapOut {
  topic_count: number
  hours: number
  weeks: number
  following: boolean
  progress: Progress | null
  next_item: OutlineItem | null
  schedule: ScheduledCourseBrief[]
}

export interface Enrollment {
  roadmap_id: number
  roadmap_name: string
  started_at: string
}

export type Finish = 'todo' | 'progress' | 'complete'

export interface RoadMapDetail extends RoadMapOut {
  enrollment: Enrollment | null
  progress: Progress | null
  schedule: ScheduledCourse[]
  sections: OutlineSection[]
  next_item: OutlineItem | null
  resources: Resource[]
  finish: Finish
  total_weeks: number
  total_topics: number
  total_hours: number
}

export interface CompletionRecord {
  topic_id: number
  completed_at: string
}

export interface CompletionResult {
  completed: boolean
  progress: Progress
  course: Progress
}

export type NoteTargetModel = 'course' | 'chapter' | 'topic' | 'roadmap' | 'resource'

export interface Note {
  id: number
  title: string
  body: string
  object_id: number
  app_label: string
  model: string
  created_at: string
  updated_at: string
}

export interface TargetNotes {
  target: { app_label: string; model: string; object_id: number; title: string; kind: string }
  notes: Note[]
}

/** django-ninja's 422 body. */
export interface ValidationErrorBody {
  detail: { loc: (string | number)[]; msg: string; type: string }[]
}
