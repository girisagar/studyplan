import { useState, type FormEvent } from 'react'
import { useParams } from 'react-router'
import { api, ApiError, errorMessage } from '../api/client'
import type { Note, TargetNotes } from '../api/types'
import { Icon } from '../components/Icon'
import { toast } from '../components/toast'
import { DataState, Page, Rich } from '../components/ui'
import { formatDate } from '../domain/format'
import { useOnline } from '../hooks/useOnline'
import { useApi } from '../offline/cache'

/** Plain text (blank line = new paragraph) -> the HTML the API stores. */
function textToHtml(text: string) {
  const escape = (s: string) =>
    s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  return text
    .trim()
    .split(/\n{2,}/)
    .map((p) => `<p>${escape(p).replace(/\n/g, '<br>')}</p>`)
    .join('')
}

function htmlToText(html: string) {
  const doc = new DOMParser().parseFromString(
    html.replace(/<br\s*\/?>/gi, '\n').replace(/<\/(p|li|h\d|blockquote|pre)>/gi, '\n\n'),
    'text/html',
  )
  return (doc.body.textContent ?? '').replace(/\n{3,}/g, '\n\n').trim()
}

export function NotesPage() {
  const { app = '', model = '', id = '' } = useParams()
  const path = `/notes/${app}/${model}/${id}`
  const { data, loading, error, refresh } = useApi<TargetNotes>(path, 0)
  const online = useOnline()
  const [editing, setEditing] = useState<Note | null>(null)
  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [errors, setErrors] = useState<Record<string, string[]>>({})
  const [busy, setBusy] = useState(false)

  function startEdit(note: Note | null) {
    setEditing(note)
    setTitle(note?.title ?? '')
    setBody(note ? htmlToText(note.body) : '')
    setErrors({})
  }

  async function save(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setErrors({})
    try {
      const payload = { title, body: textToHtml(body) }
      if (editing) await api(`/notes/${editing.id}`, { method: 'PUT', body: payload })
      else await api(path, { method: 'POST', body: payload })
      startEdit(null)
      await refresh()
      toast('Note saved.', 'success')
    } catch (e) {
      if (e instanceof ApiError && e.status === 422) setErrors(e.fieldErrors)
      else toast(errorMessage(e), 'error')
    } finally {
      setBusy(false)
    }
  }

  async function remove(note: Note) {
    if (!confirm('Delete this note?')) return
    try {
      await api(`/notes/${note.id}`, { method: 'DELETE' })
      if (editing?.id === note.id) startEdit(null)
      await refresh()
    } catch (e) {
      toast(errorMessage(e), 'error')
    }
  }

  return (
    <Page title="Notes" subtitle={data?.target.title} back={true}>
      {!data ? (
        <DataState loading={loading} error={error} />
      ) : (
        <>
          <form className="card form" onSubmit={save}>
            <h2>{editing ? 'Edit note' : `New note on this ${data.target.kind}`}</h2>
            {!online && <p className="form-note">Writing notes needs a connection.</p>}
            <label>
              Title (optional)
              <input value={title} onChange={(e) => setTitle(e.target.value)} maxLength={255} />
            </label>
            <label>
              Note
              <textarea value={body} onChange={(e) => setBody(e.target.value)} rows={6} required />
              {[...(errors.body ?? []), ...(errors.title ?? [])].map((m) => (
                <span key={m} className="field-error">
                  {m}
                </span>
              ))}
            </label>
            <div className="row gap">
              <button className="btn btn-primary" disabled={busy || !online}>
                {busy ? 'Saving…' : 'Save note'}
              </button>
              {editing && (
                <button type="button" className="btn" onClick={() => startEdit(null)}>
                  Cancel
                </button>
              )}
            </div>
          </form>
          {data.notes.map((note) => (
            <article key={note.id} className="card note">
              <div className="row between">
                <strong>{note.title || 'Note'}</strong>
                <span className="row gap-sm">
                  <button className="icon-btn" aria-label="Edit note" disabled={!online} onClick={() => startEdit(note)}>
                    <Icon name="edit" size={16} />
                  </button>
                  <button className="icon-btn" aria-label="Delete note" disabled={!online} onClick={() => void remove(note)}>
                    <Icon name="trash" size={16} />
                  </button>
                </span>
              </div>
              <Rich html={note.body} />
              <div className="muted small">Updated {formatDate(note.updated_at)}</div>
            </article>
          ))}
          {!data.notes.length && <p className="muted center">No notes yet.</p>}
        </>
      )}
    </Page>
  )
}
