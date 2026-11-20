// In-app PDF reader (PDF.js). Loads the file through fetch, so a downloaded
// file is served from the offline cache by the service worker. Pages render
// lazily as they scroll into view; zoom re-renders at the new width. Mount it
// with key={url} so switching files starts fresh.
import { getDocument, GlobalWorkerOptions, type PDFDocumentProxy } from 'pdfjs-dist'
import workerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url'
import { useEffect, useRef, useState } from 'react'
import { Icon } from './Icon'
import { Spinner } from './ui'

GlobalWorkerOptions.workerSrc = workerUrl

export default function PdfViewer({ url, title }: { url: string; title: string }) {
  const [doc, setDoc] = useState<PDFDocumentProxy | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [zoom, setZoom] = useState(1)
  const [page, setPage] = useState(1)
  const [width, setWidth] = useState(0)
  const container = useRef<HTMLDivElement>(null)

  useEffect(() => {
    let cancelled = false
    let task: ReturnType<typeof getDocument> | null = null
    ;(async () => {
      try {
        const response = await fetch(url)
        if (!response.ok) throw new Error(`Couldn't load the file (${response.status}).`)
        const data = new Uint8Array(await response.arrayBuffer())
        if (cancelled) return
        task = getDocument({
          data,
          cMapUrl: '/pdfjs/cmaps/',
          cMapPacked: true,
          standardFontDataUrl: '/pdfjs/standard_fonts/',
          wasmUrl: '/pdfjs/wasm/',
        })
        const loaded = await task.promise
        if (!cancelled) setDoc(loaded)
      } catch (e) {
        if (!cancelled) {
          setError(
            navigator.onLine
              ? (e as Error).message || "Couldn't open this PDF."
              : 'This file is not downloaded. Download it while online to read it offline.',
          )
        }
      }
    })()
    return () => {
      cancelled = true
      void task?.destroy()
    }
  }, [url])

  useEffect(() => {
    const element = container.current
    if (!element) return
    const observer = new ResizeObserver(([entry]) => setWidth(Math.floor(entry.contentRect.width)))
    observer.observe(element)
    return () => observer.disconnect()
  }, [])

  return (
    <div className="pdf">
      <div className="pdf-toolbar">
        <span className="muted small">{doc ? `Page ${page} / ${doc.numPages}` : title}</span>
        <div className="row gap-sm">
          <button className="icon-btn" aria-label="Zoom out" onClick={() => setZoom((z) => Math.max(0.5, z - 0.25))}>
            <Icon name="minus" />
          </button>
          <span className="small">{Math.round(zoom * 100)}%</span>
          <button className="icon-btn" aria-label="Zoom in" onClick={() => setZoom((z) => Math.min(3, z + 0.25))}>
            <Icon name="plus" />
          </button>
        </div>
      </div>
      <div className="pdf-pages" ref={container}>
        {error && <p className="form-error">{error}</p>}
        {!doc && !error && <Spinner label="Opening…" />}
        {doc &&
          width > 0 &&
          Array.from({ length: doc.numPages }, (_, i) => (
            <PdfPage key={i} doc={doc} number={i + 1} width={width * zoom} onVisible={setPage} />
          ))}
      </div>
    </div>
  )
}

function PdfPage({
  doc,
  number,
  width,
  onVisible,
}: {
  doc: PDFDocumentProxy
  number: number
  width: number
  onVisible: (page: number) => void
}) {
  const wrapper = useRef<HTMLDivElement>(null)
  const canvas = useRef<HTMLCanvasElement>(null)
  const [ratio, setRatio] = useState(1.294) // A4/Letter-ish until measured
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const element = wrapper.current
    if (!element) return
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true)
          if (entry.intersectionRatio > 0.4) onVisible(number)
        }
      },
      { rootMargin: '600px 0px', threshold: [0, 0.4] },
    )
    observer.observe(element)
    return () => observer.disconnect()
  }, [number, onVisible])

  useEffect(() => {
    if (!visible || !canvas.current) return
    let cancelled = false
    let task: { cancel: () => void } | null = null
    void (async () => {
      const page = await doc.getPage(number)
      if (cancelled || !canvas.current) return
      const base = page.getViewport({ scale: 1 })
      setRatio(base.height / base.width)
      const scale = (width / base.width) * (window.devicePixelRatio || 1)
      const viewport = page.getViewport({ scale })
      const target = canvas.current
      target.width = Math.floor(viewport.width)
      target.height = Math.floor(viewport.height)
      const render = page.render({ canvas: target, viewport })
      task = render
      await render.promise.catch(() => {})
    })()
    return () => {
      cancelled = true
      task?.cancel()
    }
  }, [doc, number, width, visible])

  return (
    <div className="pdf-page" ref={wrapper} style={{ width, height: width * ratio }}>
      <canvas ref={canvas} style={{ width: '100%', height: '100%' }} aria-label={`Page ${number}`} />
    </div>
  )
}
