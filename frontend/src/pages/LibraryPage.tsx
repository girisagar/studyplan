import { useMemo } from 'react'
import { Link, useParams, useSearchParams } from 'react-router'
import type { Kind, ResourceDetail, ResourceListItem } from '../api/types'
import { Icon } from '../components/Icon'
import { DownloadButton, ResourceList } from '../components/ResourceItem'
import { Chip, DataState, Empty, NoteLink, Page } from '../components/ui'
import { formatBytes, formatDate } from '../domain/format'
import { useOnline } from '../hooks/useOnline'
import { useApi } from '../offline/cache'
import { useFiles } from '../offline/files'

export function LibraryPage() {
  const { data, loading, error } = useApi<ResourceListItem[]>('/library/resources')
  const kinds = useApi<Kind[]>('/library/kinds').data ?? []
  const files = useFiles()
  const [params, setParams] = useSearchParams()
  const kind = params.get('kind') ?? ''
  const query = params.get('q') ?? ''
  const savedOnly = params.get('saved') === '1'

  const set = (key: string, value: string) => {
    const next = new URLSearchParams(params)
    if (value) next.set(key, value)
    else next.delete(key)
    setParams(next, { replace: true })
  }

  const results = useMemo(() => {
    const q = query.trim().toLowerCase()
    return (data ?? []).filter(
      (r) =>
        (!kind || r.kind === kind) &&
        (!savedOnly || (r.file_url && files.has(r.file_url))) &&
        (!q || r.title.toLowerCase().includes(q) || r.author.toLowerCase().includes(q)),
    )
  }, [data, kind, query, savedOnly, files])

  return (
    <Page title="Library">
      <div className="search">
        <Icon name="search" size={18} />
        <input
          type="search"
          placeholder="Search titles and authors"
          value={query}
          onChange={(e) => set('q', e.target.value)}
          aria-label="Search the library"
        />
      </div>
      <div className="chips filter-chips">
        <button className={`chip-btn${!kind && !savedOnly ? ' active' : ''}`} onClick={() => setParams({}, { replace: true })}>
          All
        </button>
        <button className={`chip-btn${savedOnly ? ' active' : ''}`} onClick={() => set('saved', savedOnly ? '' : '1')}>
          <Icon name="download" size={14} /> Downloaded ({files.size})
        </button>
        {kinds.map((k) => (
          <button
            key={k.value}
            className={`chip-btn${kind === k.value ? ' active' : ''}`}
            onClick={() => set('kind', kind === k.value ? '' : k.value)}
          >
            {k.label}
          </button>
        ))}
      </div>
      {!data ? (
        <DataState loading={loading} error={error} />
      ) : results.length ? (
        <div className="card">
          <ResourceList resources={results} readFrom="/library" />
        </div>
      ) : (
        <Empty icon="search" title="Nothing found">
          {savedOnly ? 'No downloaded files match. Use the download button to keep files offline.' : 'Try another search or filter.'}
        </Empty>
      )}
    </Page>
  )
}

export function ResourceDetailPage() {
  const id = Number(useParams().id)
  const { data, loading, error } = useApi<ResourceDetail>(`/library/resources/${id}`)
  const files = useFiles()
  const online = useOnline()
  if (!data) {
    return (
      <Page title="Resource" back="/library">
        <DataState loading={loading} error={error} />
      </Page>
    )
  }
  const { resource } = data
  const saved = resource.file_url ? files.get(resource.file_url) : undefined
  const available = online || !!saved
  return (
    <Page
      title={resource.title}
      back={true}
      actions={<NoteLink appLabel="library" model="resource" id={resource.id} count={data.note_count} />}
    >
      <section className="card resource-hero">
        {resource.thumbnail_url && <img src={resource.thumbnail_url} alt="" className="cover" />}
        <div>
          <div className="eyebrow">{resource.kind_label}</div>
          <h2>{resource.title}</h2>
          {resource.author && <p className="muted">{resource.author}</p>}
          <div className="row gap wrap">
            {resource.is_pdf && (
              <Link className={`btn btn-primary${available ? '' : ' disabled'}`} to={`/library/${resource.id}/read`}>
                Read
              </Link>
            )}
            {resource.href && (
              <a
                className={`btn${available ? '' : ' disabled'}`}
                href={resource.href}
                target="_blank"
                rel="noopener noreferrer"
              >
                {resource.file_url ? 'Open file' : 'Open link'} <Icon name="external" size={14} />
              </a>
            )}
            {resource.file_url && resource.url && (
              <a className={`btn${online ? '' : ' disabled'}`} href={resource.url} target="_blank" rel="noopener noreferrer">
                Website <Icon name="external" size={14} />
              </a>
            )}
          </div>
          {resource.file_url && (
            <div className="offline-row">
              <DownloadButton resource={resource} />
              <span className="muted small">
                {saved
                  ? `Available offline · ${formatBytes(saved.size)} · saved ${formatDate(saved.savedAt)}`
                  : 'Download to read it offline'}
              </span>
            </div>
          )}
        </div>
      </section>

      {(data.placements.length > 0 || data.topics.length > 0 || data.chapters.length > 0) && (
        <>
          <h2 className="section-title">Used in</h2>
          <div className="card">
            <ul className="plain-list">
              {data.placements.map((p) => (
                <li key={`${p.roadmap.id}-${p.course.id}`}>
                  <Link to={`/roadmaps/${p.roadmap.id}/courses/${p.course.id}`}>{p.course.name}</Link>{' '}
                  <span className="muted small">in {p.roadmap.name}</span>
                </li>
              ))}
              {data.chapters.map((c) => (
                <li key={`c-${c.id}-${c.roadmap.id}`}>
                  <Link to={`/roadmaps/${c.roadmap.id}/courses/${c.course.id}?week=${c.week}`}>{c.name}</Link>{' '}
                  <Chip>Week {c.week}</Chip> <span className="muted small">{c.course.name}</span>
                </li>
              ))}
              {data.topics.map((t) => (
                <li key={`t-${t.id}-${t.roadmap.id}`}>
                  <Link to={`/roadmaps/${t.roadmap.id}/courses/${t.course.id}?topic=${t.id}`}>{t.topic_name}</Link>{' '}
                  <Chip>Week {t.week}</Chip> <span className="muted small">{t.chapter.name}</span>
                </li>
              ))}
            </ul>
          </div>
        </>
      )}
    </Page>
  )
}
