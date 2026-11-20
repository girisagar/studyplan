import { Link } from 'react-router'
import { PendingBadge } from '../components/PendingBadge'
import { playerPath } from '../domain/paths'
import { Chip, Empty, Page, ProgressBar, ProgressSummary } from '../components/ui'
import { weeklyCounts } from '../domain/derive'
import { PACE_LABEL, timeAgo } from '../domain/format'
import { useLearning } from '../hooks/useData'

export function ProgressPage() {
  const { snapshots, stats, topics, local } = useLearning()
  const weeks = weeklyCounts(local)
  const peak = Math.max(1, ...weeks.map((w) => w.count))
  const recent = [...local.done.entries()]
    .sort((a, b) => b[1].localeCompare(a[1]))
    .slice(0, 12)
    .map(([topicId, at]) => ({ at, entry: topics.get(topicId), topicId }))

  return (
    <Page title="Progress">
      <section className="stats">
        <div className="stat card">
          <span className="stat-value">{stats.completed}</span>
          <span className="stat-label">Topics done</span>
        </div>
        <div className="stat card">
          <span className="stat-value">{stats.thisWeek}</span>
          <span className="stat-label">This week</span>
        </div>
        <div className="stat card">
          <span className="stat-value">{stats.hoursDone}</span>
          <span className="stat-label">Hours (est.)</span>
        </div>
      </section>

      <h2 className="section-title">Last 8 weeks</h2>
      <div className="card chart" role="img" aria-label="Topics completed per week">
        {weeks.map((w) => (
          <div key={w.start.toISOString()} className="chart-col">
            <span className="chart-count">{w.count || ''}</span>
            <div className="chart-bar" style={{ height: `${(100 * w.count) / peak}%` }} />
            <span className="chart-label">
              {w.start.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
            </span>
          </div>
        ))}
      </div>

      <h2 className="section-title">Roadmaps</h2>
      {snapshots.length ? (
        snapshots.map((s) => (
          <section key={s.view.roadmap.id} className="card">
            <div className="row between">
              <Link to={`/roadmaps/${s.view.roadmap.id}`}>
                <strong>{s.view.roadmap.name}</strong>
              </Link>
              {s.pace && <Chip tone={s.pace === 'behind' ? 'warning' : 'success'}>{PACE_LABEL[s.pace]}</Chip>}
            </div>
            <ProgressSummary progress={s.view.progress} />
            <div className="muted small">
              {s.hoursDone}/{s.hoursTotal}h
              {s.scheduledWeek ? ` · schedule expects week ${s.scheduledWeek}` : ''}
              {s.view.next ? ` · next is in week ${s.view.next.week}` : ''}
            </div>
            <ul className="course-progress">
              {s.view.schedule.map((c) => (
                <li key={c.course.id}>
                  <Link to={`/roadmaps/${s.view.roadmap.id}/courses/${c.course.id}`}>{c.course.name}</Link>
                  <ProgressBar value={c.progress.percent} label={c.course.name} />
                  <span className="muted small">
                    {c.progress.completed}/{c.progress.total}
                  </span>
                </li>
              ))}
            </ul>
          </section>
        ))
      ) : (
        <Empty icon="chart" title="No roadmaps followed yet">
          <Link to="/roadmaps">Browse roadmaps</Link> to start tracking.
        </Empty>
      )}

      <h2 className="section-title">Recent activity</h2>
      {recent.length ? (
        <div className="card">
          <ul className="plain-list">
            {recent.map(({ at, entry, topicId }) => (
              <li key={topicId} className="row between">
                {entry ? (
                  <Link to={playerPath(entry.view.roadmap.id, entry.item)}>
                    {entry.item.topic.topic_name}
                    <span className="muted small"> · {entry.item.course.name}</span>
                  </Link>
                ) : (
                  <span>Topic #{topicId}</span>
                )}
                <span className="muted small row gap-sm">
                  {local.pendingTopics.has(topicId) && <PendingBadge topicId={topicId} />}
                  {timeAgo(at)}
                </span>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <p className="muted">Completed topics will show up here.</p>
      )}
    </Page>
  )
}
