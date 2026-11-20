/// <reference lib="webworker" />
// Service worker (vite-plugin-pwa, injectManifest).
//  * App shell and static assets: precached; navigations get index.html (SPA).
//  * /api/: never cached here — the app keeps its own per-user copy in IndexedDB.
//  * /media/: answered from the downloaded-files cache when present, otherwise
//    from the network without storing (downloads are explicit, see offline/files.ts).
import { cleanupOutdatedCaches, createHandlerBoundToURL, precacheAndRoute } from 'workbox-precaching'
import { NavigationRoute, registerRoute } from 'workbox-routing'
import { CacheFirst } from 'workbox-strategies'
import { ExpirationPlugin } from 'workbox-expiration'
import { FILES_CACHE } from './offline/constants'

declare const self: ServiceWorkerGlobalScope & {
  __WB_MANIFEST: (string | { url: string; revision: string | null })[]
}

precacheAndRoute(self.__WB_MANIFEST)
cleanupOutdatedCaches()

registerRoute(
  new NavigationRoute(createHandlerBoundToURL('/index.html'), {
    denylist: [/^\/api\//, /^\/media\//, /^\/admin/, /^\/static\//, /^\/ckeditor5\//],
  }),
)

const isThumbnail = (url: URL) => url.pathname.startsWith('/media/resource_thumbnails/')

registerRoute(
  ({ url, request }) => request.method === 'GET' && url.pathname.startsWith('/media/') && !isThumbnail(url),
  async ({ request }) => {
    const cache = await caches.open(FILES_CACHE)
    const hit = await cache.match(request.url, { ignoreSearch: true, ignoreVary: true })
    return hit ?? fetch(request)
  },
)

registerRoute(
  ({ url }) => isThumbnail(url),
  new CacheFirst({
    cacheName: 'studyplan-thumbnails',
    plugins: [new ExpirationPlugin({ maxEntries: 200, maxAgeSeconds: 60 * 24 * 3600 })],
  }),
)

// PDF.js character maps (only some CJK PDFs need them): cache on first use.
registerRoute(
  ({ url }) => url.pathname.startsWith('/pdfjs/cmaps/'),
  new CacheFirst({ cacheName: 'studyplan-pdfjs-cmaps' }),
)

self.addEventListener('message', (event) => {
  if (event.data?.type === 'SKIP_WAITING') void self.skipWaiting()
})
