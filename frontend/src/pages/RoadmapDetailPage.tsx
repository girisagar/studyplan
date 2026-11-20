import { useMemo } from 'react'
import { Link, useParams } from 'react-router'
import type { CourseDetail, Resource } from '../api/types'
import { FollowButton } from '../components/FollowButton'
import { DownloadAllButton, ResourceList } from '../components/ResourceItem'
import { TopicRow } from '../components/TopicRow'
import { playerPath } from '../domain/paths'
import { Chip, DataState, NoteLink, Page, ProgressBar, ProgressSummary, Rich } from '../components/ui'
import { plural } from '../domain/format'
import { useRoadmapView } from '../hooks/useData'
import { readCache, useCacheVersion } from '../offline/cache'

const STATE_LABEL = { done: '✓ Completed', current: 'Up next', upcoming: 'Not started' }

/** Every resource with a file across the given courses (course, chapters, topics). */
function useCourseFiles(courseIds: number[]): Resource[] {
  const version = useCacheVersion()
  const key = courseIds.join(',')
  return useMemo(() => {
    void version
    const all: Resource[] = []
    for (const id of key ? key.split(',').map(Number) : []) {
      const course = readCache<CourseDetail>(`/curriculum/courses/${id}`)?.data
      if (!course) continue
      all.push(...course.resources)
      for (const chapter of course.chapters) {
        all.push(...chapter.resources)
        for (const topic of chapter.topics) all.push(...topic.resources)
      }
    }
    const seen = new Set<string>()
    return all.filter((r) => r.file_url && !seen.has(r.file_url) && seen.add(r.file_url))
  }, [version, key])
}

export function RoadmapDetailPage() {
  const id = Number(useParams().id)
  const { view, loading, error } = useRoadmapView(id)
  const files = useCourseFiles(view?.schedule.map((s) => s.course.id) ?? [])

  if (!view) {
    return (
      <Page title="Roadmap" back="/roadmaps">
        <DataState loading={loading} error={error} />
      </Page>
    )
  }
  const { roadmap, following, progress } = view

  return (
    <Page
      title={roadmap.name}
      back="/roadmaps"
      actions={<NoteLink appLabel="roadmaps" model="roadmap" id={roadmap.id} count={roadmap.note_count} />}
    >
      <section className="card">
        <Rich html={roadmap.description} />
        <div className="muted small">
          {plural(roadmap.total_weeks, 'week')} · {plural(roadmap.total_topics, 'topic')} ·{' '}
          {roadmap.total_hours}h estimated
        </div>
        {following && <ProgressSummary progress={progress} label="In progress" />}
        <div className="row gap wrap">
          {following ? (
            view.next && (
              <>
                <Link className="btn btn-primary" to={playerPath(roadmap.id, view.next)}>
                  {progress.completed ? 'Continue' : 'Start'}
                </Link>
                <span className="muted small next-line">
                  Next: week {view.next.week} · {view.next.topic.topic_name}
                </span>
              </>
            )
          ) : (
            <FollowButton roadmap={roadmap} />
          )}
          <DownloadAllButton resources={files} label="Download all files" />
        </div>
      </section>

      <h2 className="section-title">Courses</h2>
      <ol className="timeline">
        {view.schedule.map((link) => (
          <li key={link.course.id} className={`timeline-item state-${following ? link.state : 'upcoming'}`}>
            <Link to={`/roadmaps/${roadmap.id}/courses/${link.course.id}`} className="card card-link">
              <div className="row between">
                <div>
                  <div className="eyebrow">
                    Weeks {link.first_week}–{link.last_week}
                  </div>
                  <strong>{link.course.name}</strong>
                </div>
                {following && <span className="muted small timeline-state">{STATE_LABEL[link.state]}</span>}
              </div>
              <div className="muted small">
                {plural(link.topic_count, 'topic')} · {link.hours}h
              </div>
              {following && (
                <>
                  <ProgressBar value={link.progress.percent} label={link.course.name} />
                  <span className="muted small">
                    {link.progress.completed}/{link.progress.total} · {link.progress.percent}%
                  </span>
                </>
              )}
            </Link>
          </li>
        ))}
        <li className={`timeline-item timeline-finish finish-${view.finish}`}>
          <span>
            {view.finish === 'complete' ? 'Roadmap complete 🎉' : `Finish · week ${roadmap.total_weeks}`}
          </span>
        </li>
      </ol>

      <h2 className="section-title">Week by week</h2>
      <div className="outline">
        {view.sections.map((section) => (
          <details
            key={section.week}
            className="card week"
            open={following && view.next?.week === section.week}
          >
            <summary>
              <span className="week-number">W{section.week}</span>
              <span className="week-title">
                <strong>{section.title}</strong>
                <span className="muted small">
                  {section.courses.map((c) => c.name).join(' · ')} · {section.hours}h
                </span>
              </span>
              {following && (
                <Chip tone={section.percent === 100 ? 'success' : undefined}>
                  {section.completed}/{section.total}
                </Chip>
              )}
            </summary>
            {section.groups.map((group) => (
              <div key={group.chapter.id} className="outline-group">
                <div className="outline-group-head">
                  <span className="muted small">
                    {group.course.name}
                    {group.chapter.position ? ` · Chapter ${group.chapter.position}` : ''}
                  </span>
                  <strong>{group.chapter.name}</strong>
                </div>
                <ul className="topic-list">
                  {group.items.map((item) => (
                    <TopicRow key={item.topic.id} item={item} roadmapId={roadmap.id} following={following} />
                  ))}
                </ul>
              </div>
            ))}
          </details>
        ))}
      </div>

      {roadmap.resources.length > 0 && (
        <>
          <h2 className="section-title">Course materials</h2>
          <div className="card">
            <ResourceList resources={roadmap.resources} readFrom={`/roadmaps/${roadmap.id}`} />
          </div>
        </>
      )}
    </Page>
  )
}
