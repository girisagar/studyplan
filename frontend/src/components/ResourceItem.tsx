import { useState } from 'react'
import { Link } from 'react-router'
import type { Resource } from '../api/types'
import { formatBytes } from '../domain/format'
import { useOnline } from '../hooks/useOnline'
import { downloadAll, downloadFile, removeFile, useDownloadProgress, useFiles } from '../offline/files'
import { Icon, type IconName } from './Icon'
import { toast } from './toast'

function iconFor(resource: Resource): IconName {
  if (resource.kind === 'video') return 'play'
  if (resource.kind === 'book') return 'book'
  return resource.file_url ? 'file' : 'link'
}

export function DownloadButton({ resource }: { resource: Resource }) {
  const files = useFiles()
  const progress = useDownloadProgress()
  const online = useOnline()
  const url = resource.file_url
  if (!url) return null
  const saved = files.get(url)
  const fraction = progress.get(url)
  if (fraction !== undefined) {
    return (
      <span className="dl-progress" title="Downloading">
        <span className="spinner" aria-hidden="true" />
        {Math.round(fraction * 100)}%
      </span>
    )
  }
  if (saved) {
    return (
      <button
        className="icon-btn dl-saved"
        title={`Available offline (${formatBytes(saved.size)}). Click to remove.`}
        aria-label="Remove offline copy"
        onClick={async () => {
          if (confirm(`Remove the offline copy of “${resource.title}”?`)) await removeFile(url)
        }}
      >
        <Icon name="check" size={18} />
      </button>
    )
  }
  return (
    <button
      className="icon-btn"
      title="Download for offline use"
      aria-label="Download for offline use"
      disabled={!online}
      onClick={async () => {
        try {
          await downloadFile(resource)
          toast(`“${resource.title}” is available offline.`, 'success')
        } catch (error) {
          toast(error instanceof Error ? error.message : 'Download failed.', 'error')
        }
      }}
    >
      <Icon name="download" size={18} />
    </button>
  )
}

export function ResourceItem({ resource, readFrom }: { resource: Resource; readFrom?: string }) {
  const files = useFiles()
  const online = useOnline()
  const saved = resource.file_url ? files.has(resource.file_url) : false
  const available = online || saved
  const reader = `/library/${resource.id}/read${readFrom ? `?from=${encodeURIComponent(readFrom)}` : ''}`
  return (
    <li className="resource">
      <Link to={`/library/${resource.id}`} className="resource-icon" aria-hidden="true" tabIndex={-1}>
        <Icon name={iconFor(resource)} />
      </Link>
      <div className="resource-body">
        <Link to={`/library/${resource.id}`} className="resource-title">
          {resource.title}
        </Link>
        <div className="resource-meta">
          {[resource.kind_label, resource.author].filter(Boolean).join(' · ')}
          {saved && <span className="offline-tag">Offline</span>}
        </div>
      </div>
      <div className="resource-actions">
        {resource.is_pdf ? (
          <Link className={`btn btn-sm${available ? '' : ' disabled'}`} to={reader}>
            Read
          </Link>
        ) : (
          resource.href && (
            <a
              className={`btn btn-sm${available ? '' : ' disabled'}`}
              href={resource.href}
              target="_blank"
              rel="noopener noreferrer"
            >
              Open <Icon name="external" size={14} />
            </a>
          )
        )}
        <DownloadButton resource={resource} />
      </div>
    </li>
  )
}

export function ResourceList({ resources, readFrom }: { resources: Resource[]; readFrom?: string }) {
  if (!resources.length) return null
  return (
    <ul className="resources">
      {resources.map((r) => (
        <ResourceItem key={r.id} resource={r} readFrom={readFrom} />
      ))}
    </ul>
  )
}

/** "Download all" for a set of resources (only those with uploaded files). */
export function DownloadAllButton({ resources, label = 'Download files' }: { resources: Resource[]; label?: string }) {
  const files = useFiles()
  const online = useOnline()
  const [busy, setBusy] = useState<{ done: number; total: number } | null>(null)
  const withFiles = resources.filter((r) => r.file_url)
  const missing = withFiles.filter((r) => !files.has(r.file_url!))
  if (!withFiles.length) return null
  if (!missing.length && !busy) {
    return (
      <span className="chip chip-success">
        <Icon name="check" size={14} /> All {withFiles.length} files offline
      </span>
    )
  }
  return (
    <button
      className="btn btn-sm"
      disabled={!online || !!busy}
      onClick={async () => {
        setBusy({ done: 0, total: missing.length })
        try {
          await downloadAll(missing, (done) => setBusy({ done, total: missing.length }))
          toast(`${missing.length} files are available offline.`, 'success')
        } catch (error) {
          toast(error instanceof Error ? error.message : 'Download failed.', 'error')
        } finally {
          setBusy(null)
        }
      }}
    >
      <Icon name="download" size={16} />
      {busy ? `Downloading ${busy.done}/${busy.total}…` : `${label} (${missing.length})`}
    </button>
  )
}
