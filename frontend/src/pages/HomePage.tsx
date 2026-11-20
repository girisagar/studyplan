import { Link } from 'react-router'
import { useSession } from '../auth/session'
import { TopicRow } from '../components/TopicRow'
import { playerPath } from '../domain/paths'
import { Chip, Empty, Page, ProgressBar, ProgressRing, Spinner } from '../components/ui'
import { greeting, PACE_LABEL, plural } from '../domain/format'
import { useLearning } from '../hooks/useData'
import { useSyncStatus } from '../offline/sync'
import { RoadmapCards } from './RoadmapsPage'

export function HomePage() {
  const session = useSession()
  const { views, snapshots, stats } = useLearning()
  const sync = useSyncStatus()

  if (!session) {
    return (
      <Page title="Learning Roadmap">
        <section className="hero card">
          <h2>Study on a schedule — even offline.</h2>
          <p className="muted">
            Follow a roadmap of courses week by week, check off topics, and download the books
            to read anywhere. Progress you record offline syncs when you reconnect.
          </p>
          <div className="row gap">
            <Link className="btn btn-primary" to="/register">
              Create account
            </Link>
            <Link className="btn" to="/login">
              Sign in
            </Link>
          </div>
        </section>
        <h2 className="section-title">Roadmaps</h2>
        <RoadmapCards />
      </Page>
    )
  }

  const active = snapshots[0]
  const others = snapshots.slice(1)
  const waitingForData = !views.length && sync.phase === 'syncing'

  return (
    <Page title={`${greeting()}, ${session.user.username}`}>
      {waitingForData && <Spinner label="Preparing your roadmaps for offline use…" />}
      {active ? (
        <>
          <section className="card continue">
            <div className="continue-head">
              <div>
                <div className="eyebrow">Continue learning</div>
                <h2>
                  <Link to={`/roadmaps/${active.view.roadmap.id}`}>{active.view.roadmap.name}</Link>
                </h2>
                {active.pace && (
                  <Chip tone={active.pace === 'behind' ? 'warning' : 'success'}>
                    {PACE_LABEL[active.pace]}
                    {active.scheduledWeek && active.pace !== 'done'
                      ? ` · schedule: week ${active.scheduledWeek}`
                      : ''}
                  </Chip>
                )}
              </div>
              <ProgressRing value={active.view.progress.percent} />
            </div>
            {active.view.next ? (
              <Link
                className="next-topic"
                to={playerPath(active.view.roadmap.id, active.view.next)}
              >
                <span className="muted small">
                  Week {active.view.next.week} · {active.view.next.course.name} ·{' '}
                  {active.view.next.chapter.name}
                </span>
                <strong>{active.view.next.topic.topic_name}</strong>
                <span className="btn btn-primary btn-sm">Continue</span>
              </Link>
            ) : (
              <p>You've completed every topic in this roadmap. 🎉</p>
            )}
            <div className="muted small">
              {active.hoursDone} of {active.hoursTotal} estimated hours ·{' '}
              {plural(active.view.progress.completed, 'topic')} done
            </div>
          </section>

          {active.currentSection && (
            <section>
              <h2 className="section-title">
                Week {active.currentSection.week}
                <span className="muted small">
                  {' '}
                  · {active.currentSection.completed}/{active.currentSection.total} done ·{' '}
                  {active.currentSection.hours}h
                </span>
              </h2>
              <div className="card">
                {active.currentSection.groups.map((group) => (
                  <div key={group.chapter.id} className="outline-group">
                    <div className="outline-group-head">
                      <span className="muted small">{group.course.name}</span>
                      <strong>{group.chapter.name}</strong>
                    </div>
                    <ul className="topic-list">
                      {group.items.map((item) => (
                        <TopicRow
                          key={item.topic.id}
                          item={item}
                          roadmapId={active.view.roadmap.id}
                          following
                        />
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </section>
          )}
        </>
      ) : (
        !waitingForData && (
          <Empty icon="map" title="Pick a roadmap to start">
            Follow a roadmap to track progress and get a weekly plan.
          </Empty>
        )
      )}

      <section className="stats">
        <Stat value={stats.completed} label="Topics done" />
        <Stat value={stats.thisWeek} label="This week" />
        <Stat value={stats.hoursDone} label="Hours (est.)" />
        <Stat value={snapshots.length} label="Following" />
      </section>

      {others.length > 0 && (
        <section>
          <h2 className="section-title">Your other roadmaps</h2>
          <div className="cards">
            {others.map((s) => (
              <Link key={s.view.roadmap.id} to={`/roadmaps/${s.view.roadmap.id}`} className="card card-link">
                <strong>{s.view.roadmap.name}</strong>
                <ProgressBar value={s.view.progress.percent} label={s.view.roadmap.name} />
                <span className="muted small">
                  {s.view.progress.percent}% · {s.pace ? PACE_LABEL[s.pace] : ''}
                </span>
              </Link>
            ))}
          </div>
        </section>
      )}

      {!snapshots.length && (
        <section>
          <h2 className="section-title">Roadmaps</h2>
          <RoadmapCards />
        </section>
      )}
    </Page>
  )
}

function Stat({ value, label }: { value: number; label: string }) {
  return (
    <div className="stat card">
      <span className="stat-value">{value}</span>
      <span className="stat-label">{label}</span>
    </div>
  )
}
