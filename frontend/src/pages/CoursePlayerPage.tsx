import { useEffect, useMemo, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router'
import type { ChapterOut, CourseDetail, TopicOut } from '../api/types'
import { FollowButton } from '../components/FollowButton'
import { Icon } from '../components/Icon'
import { PendingBadge } from '../components/PendingBadge'
import { DownloadAllButton, ResourceList } from '../components/ResourceItem'
import { TopicRow } from '../components/TopicRow'
import { playerPath } from '../domain/paths'
import { Chip, DataState, Empty, NoteLink, Page, ProgressRing, Rich } from '../components/ui'
import { courseSections, pickItem, progressOf } from '../domain/derive'
import { useCourse, useRoadmapView } from '../hooks/useData'
import { setTopicCompleted } from '../offline/progress'

function indexCourse(course: CourseDetail | undefined) {
  const topics = new Map<number, TopicOut>()
  const chapters = new Map<number, ChapterOut>()
  for (const chapter of course?.chapters ?? []) {
    chapters.set(chapter.id, chapter)
    for (const topic of chapter.topics) topics.set(topic.id, topic)
  }
  return { topics, chapters }
}

export function CoursePlayerPage() {
  const params = useParams()
  const roadmapId = Number(params.id)
  const courseId = Number(params.courseId)
  const [search, setSearch] = useSearchParams()
  const topicParam = search.get('topic')
  const weekParam = search.get('week')
  const { view, loading, error } = useRoadmapView(roadmapId)
  const course = useCourse(courseId)
  const [outlineOpen, setOutlineOpen] = useState(false)
  const content = useMemo(() => indexCourse(course.data), [course.data])

  const sections = useMemo(() => (view ? courseSections(view, courseId) : []), [view, courseId])
  const items = useMemo(() => sections.flatMap((s) => s.groups.flatMap((g) => g.items)), [sections])
  const current = useMemo(
    () => pickItem(items, topicParam ? Number(topicParam) : null, weekParam ? Number(weekParam) : null),
    [items, topicParam, weekParam],
  )
  // Put the resolved topic in the URL, so checking it off doesn't jump ahead
  // and the address can be shared/reloaded.
  const resolvedId = current?.topic.id
  useEffect(() => {
    if (!topicParam && resolvedId !== undefined) {
      setSearch({ topic: String(resolvedId) }, { replace: true })
    }
  }, [topicParam, resolvedId, setSearch])

  const link = view?.schedule.find((s) => s.course.id === courseId)
  if (!view || !link) {
    return (
      <Page title="Course" back={`/roadmaps/${roadmapId}`}>
        {view ? <Empty title="This course isn't part of the roadmap." /> : <DataState loading={loading} error={error} />}
      </Page>
    )
  }

  const progress = progressOf(items)
  const index = current ? items.indexOf(current) : -1
  const previous = index > 0 ? items[index - 1] : null
  const next = index >= 0 && index < items.length - 1 ? items[index + 1] : null
  const topic = current ? content.topics.get(current.topic.id) : undefined
  const chapter = current ? content.chapters.get(current.chapter.id) : undefined
  const courseData = course.data
  const allFiles = courseData
    ? [
        ...courseData.resources,
        ...courseData.chapters.flatMap((c) => [...c.resources, ...c.topics.flatMap((t) => t.resources)]),
      ]
    : []
  const here = current ? playerPath(roadmapId, current) : `/roadmaps/${roadmapId}/courses/${courseId}`

  const outline = (
    <aside className={`player-outline${outlineOpen ? ' open' : ''}`} aria-label="Course outline">
      <div className="player-outline-head">
        <ProgressRing value={progress.percent} size={48} />
        <div className="player-outline-title">
          <strong>{link.course.name}</strong>
          <div className="muted small">
            Weeks {link.first_week}–{link.last_week} · {progress.completed}/{progress.total} done
          </div>
        </div>
        <button className="icon-btn sheet-close" aria-label="Close outline" onClick={() => setOutlineOpen(false)}>
          <Icon name="close" />
        </button>
      </div>
      <div className="player-outline-body">
        {sections.map((section) => (
          <div key={section.week} className="outline-week">
            <div className="outline-week-head">
              <span>Week {section.week}</span>
              <span className="muted small">
                {section.completed}/{section.total} · {section.hours}h
              </span>
            </div>
            {section.groups.map((group) => (
              <div key={group.chapter.id} className="outline-group">
                <div className="outline-group-head">
                  <strong>{group.chapter.name}</strong>
                </div>
                <ul className="topic-list">
                  {group.items.map((item) => (
                    <TopicRow
                      key={item.topic.id}
                      item={item}
                      roadmapId={roadmapId}
                      following={view.following}
                      active={item === current}
                      onOpen={() => setOutlineOpen(false)}
                    />
                  ))}
                </ul>
              </div>
            ))}
          </div>
        ))}
        {courseData && (
          <div className="outline-materials">
            <div className="row between">
              <strong>Course materials</strong>
              <DownloadAllButton resources={allFiles} label="Download all" />
            </div>
            <ResourceList resources={courseData.resources} readFrom={here} />
          </div>
        )}
      </div>
    </aside>
  )

  return (
    <Page
      wide
      back={`/roadmaps/${roadmapId}`}
      title={link.course.name}
      subtitle={<Link to={`/roadmaps/${roadmapId}`}>{view.roadmap.name}</Link>}
      actions={
        <>
          <NoteLink appLabel="curriculum" model="course" id={courseId} count={courseData?.note_count} />
          <button className="icon-btn outline-toggle" aria-label="Show outline" onClick={() => setOutlineOpen(true)}>
            <Icon name="list" size={22} />
          </button>
        </>
      }
    >
      <div className="player">
        <article className="player-topic">
          {!current ? (
            <Empty title="No topics in this course yet." />
          ) : (
            <>
              <div className="eyebrow">
                Week {current.week} · {current.chapter.name} · Topic {index + 1} of {items.length}
              </div>
              <div className="row between start">
                <h2 className="topic-title">{current.topic.topic_name}</h2>
                <NoteLink appLabel="curriculum" model="topic" id={current.topic.id} count={topic?.note_count} />
              </div>
              <div className="chips">
                <Chip>
                  <Icon name="clock" size={14} /> {current.topic.total_time}h
                </Chip>
                {current.topic.tags.map((tag) => (
                  <Chip key={tag.id}>{tag.name}</Chip>
                ))}
              </div>

              {view.following ? (
                <div className="complete-row">
                  <button
                    className={`btn ${current.completed ? 'btn-success' : 'btn-primary'}`}
                    onClick={() => void setTopicCompleted(roadmapId, current.topic.id, !current.completed)}
                  >
                    <Icon name="check" size={18} />
                    {current.completed ? 'Completed' : 'Mark as complete'}
                  </button>
                  {current.pending && <PendingBadge topicId={current.topic.id} long />}
                </div>
              ) : (
                <div className="complete-row">
                  <FollowButton roadmap={view.roadmap} label="Follow this roadmap to track progress" className="btn" />
                </div>
              )}

              {topic ? (
                <>
                  <Rich html={topic.description} />
                  {topic.resources.length > 0 && (
                    <section>
                      <h3>Resources</h3>
                      <ResourceList resources={topic.resources} readFrom={here} />
                    </section>
                  )}
                </>
              ) : (
                !course.data && <DataState loading={course.loading} error={course.error} />
              )}

              {chapter && (
                <section className="chapter-box">
                  <h3>
                    Chapter: {chapter.name}
                    <NoteLink appLabel="curriculum" model="chapter" id={chapter.id} count={chapter.note_count} />
                  </h3>
                  <Rich html={chapter.description} />
                  {chapter.deliverable && (
                    <p>
                      <strong>Deliverable:</strong> {chapter.deliverable}
                    </p>
                  )}
                  <ResourceList resources={chapter.resources} readFrom={here} />
                </section>
              )}

              <nav className="prev-next">
                {previous ? (
                  <Link className="btn" to={playerPath(roadmapId, previous)}>
                    <Icon name="back" size={16} /> Previous
                  </Link>
                ) : (
                  <span />
                )}
                {next && (
                  <Link className="btn btn-primary" to={playerPath(roadmapId, next)}>
                    Next <Icon name="next" size={16} />
                  </Link>
                )}
              </nav>
            </>
          )}
        </article>
        {outline}
        {outlineOpen && <div className="sheet-backdrop" onClick={() => setOutlineOpen(false)} />}
      </div>
    </Page>
  )
}
