import { lazy, Suspense } from 'react'
import { useParams, useSearchParams } from 'react-router'
import type { ResourceDetail, ResourceListItem } from '../api/types'
import { DownloadButton } from '../components/ResourceItem'
import { Empty, Page, Spinner } from '../components/ui'
import { useApi, useCached } from '../offline/cache'

const PdfViewer = lazy(() => import('../components/PdfViewer'))

/** Same-site path to return to (never another origin). */
function safeBack(value: string | null, fallback: string) {
  return value && value.startsWith('/') && !value.startsWith('//') ? value : fallback
}

export function ReaderPage() {
  const id = Number(useParams().id)
  const [params] = useSearchParams()
  const list = useCached<ResourceListItem[]>('/library/resources')
  const detail = useApi<ResourceDetail>(`/library/resources/${id}`)
  const resource = detail.data?.resource ?? list?.data.find((r) => r.id === id)
  const back = safeBack(params.get('from'), `/library/${id}`)

  if (!resource) {
    return (
      <Page title="Reader" back={back}>
        {detail.loading ? <Spinner /> : <Empty title="Resource not available offline" />}
      </Page>
    )
  }
  return (
    <Page wide title={resource.title} back={back} actions={<DownloadButton resource={resource} />}>
      {resource.is_pdf && resource.file_url ? (
        <Suspense fallback={<Spinner label="Loading reader…" />}>
          <PdfViewer key={resource.file_url} url={resource.file_url} title={resource.title} />
        </Suspense>
      ) : (
        <Empty title="Only uploaded PDFs open in the reader." />
      )}
    </Page>
  )
}
