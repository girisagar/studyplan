import { Link } from 'react-router'
import type { RoadMapListItem } from '../api/types'
import { FollowButton } from '../components/FollowButton'
import { playerPath } from '../domain/paths'
import { Chip, DataState, Page, ProgressSummary } from '../components/ui'
import { plural } from '../domain/format'
import { useAllRoadmapViews } from '../hooks/useData'
import { useApi } from '../offline/cache'

export function RoadmapsPage() {
  return (
    <Page title="Roadmaps">
      <RoadmapCards />
    </Page>
  )
}

export function RoadmapCards() {
  const { data, loading, error } = useApi<RoadMapListItem[]>('/roadmaps')
  const views = new Map(useAllRoadmapViews().map((v) => [v.roadmap.id, v]))
  if (!data) return <DataState loading={loading} error={error} />
  return (
    <div className="cards">
      {data.map((roadmap) => {
        const view = views.get(roadmap.id)
        const following = view?.following ?? false
        return (
          <article key={roadmap.id} className="card roadmap-card">
            <Link to={`/roadmaps/${roadmap.id}`} className="roadmap-card-title">
              <h2>{roadmap.name}</h2>
            </Link>
            <div className="muted small">
              {plural(roadmap.weeks, 'week')} · {plural(roadmap.topic_count, 'topic')} ·{' '}
              {roadmap.hours}h
            </div>
            <div className="chips">
              {roadmap.schedule.map((s) => (
                <Chip key={s.course.id}>{s.course.name}</Chip>
              ))}
            </div>
            {following && view && <ProgressSummary progress={view.progress} label="In progress" />}
            <div className="row gap">
              {following && view?.next ? (
                <Link className="btn btn-primary" to={playerPath(roadmap.id, view.next)}>
                  Continue
                </Link>
              ) : (
                !following && <FollowButton roadmap={roadmap} label="Start" />
              )}
              <Link className="btn" to={`/roadmaps/${roadmap.id}`}>
                View roadmap
              </Link>
            </div>
          </article>
        )
      })}
    </div>
  )
}
