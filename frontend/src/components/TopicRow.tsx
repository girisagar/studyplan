import { Link } from 'react-router'
import type { ItemView } from '../domain/derive'
import { playerPath } from '../domain/paths'
import { setTopicCompleted } from '../offline/progress'
import { Icon } from './Icon'
import { PendingBadge } from './PendingBadge'

/** A topic in an outline: completion check (when following) and a link. */
export function TopicRow({
  item,
  roadmapId,
  following,
  active,
  onOpen,
}: {
  item: ItemView
  roadmapId: number
  following: boolean
  active?: boolean
  onOpen?: () => void
}) {
  return (
    <li className={`topic-row${item.completed ? ' done' : ''}${active ? ' active' : ''}`}>
      {following ? (
        <button
          className="check"
          role="checkbox"
          aria-checked={item.completed}
          aria-label={`${item.completed ? 'Mark not done' : 'Mark done'}: ${item.topic.topic_name}`}
          onClick={() => void setTopicCompleted(roadmapId, item.topic.id, !item.completed)}
        >
          {item.completed && <Icon name="check" size={14} />}
        </button>
      ) : (
        <span className="topic-number">{item.number}</span>
      )}
      <Link to={playerPath(roadmapId, item)} className="topic-link" onClick={onOpen}>
        <span className="topic-name">{item.topic.topic_name}</span>
        <span className="topic-meta">
          {item.topic.total_time}h
          {item.pending && <PendingBadge topicId={item.topic.id} />}
        </span>
      </Link>
    </li>
  )
}
