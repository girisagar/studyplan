# Learning Roadmap — frontend

Installable, offline-first PWA for the study roadmap API: React 19, TypeScript 7, Vite 8,
vite-plugin-pwa (custom Workbox service worker), IndexedDB (`idb`), PDF.js reader.

## Run it

```bash
npm install                 # also copies PDF.js fonts/cmaps/wasm into public/pdfjs
npm run dev                 # http://localhost:8083 (service worker off; see below)
```

Both servers listen on `0.0.0.0:8083`, so other devices on your network can open
`http://<this-machine-ip>:8083`. Browsers only allow service workers (offline mode and
install) on `localhost` or HTTPS, so test those on a phone over an HTTPS tunnel.

The backend must be running (`cd ../backend && pipenv run python manage.py runserver`). The
dev and preview servers proxy `/api` and `/media` to it (`BACKEND_URL`, default
`http://127.0.0.1:8000`), so no CORS setup is needed and downloaded files are same-origin.

To try the PWA (install, offline, updates) use a production build:

```bash
npm run build && npm run preview   # http://localhost:8083
```

Or set `PWA_DEV=1` to enable the service worker in `npm run dev`.

| Script | |
|---|---|
| `npm run typecheck` / `npm run lint` | `tsc -b` / oxlint |
| `npm run e2e` | Playwright offline test against `npm run preview` (see `e2e/offline.mjs`; uses a real account — point the backend at a throwaway database) |

## What works offline

- **Browsing**: after the first sync the app keeps the roadmaps, week outlines, full course
  content (topics, chapters, resources) and the library in IndexedDB, and refreshes them
  whenever it is online (at start, on reconnect, when reopened, at most every 5 minutes).
- **Progress**: checking off a topic (or following a roadmap) is saved on the device
  immediately with its time, shown as “not synced”, and pushed in order when the
  connection returns. Every progress number, the next topic, pace and stats are computed
  locally from the cached outline and the local completion set.
- **Files**: the download button keeps a resource's file (PDFs and other uploads) in Cache
  Storage; the service worker serves it from there at the same URL. PDFs open in the
  in-app reader. Profile › Offline files lists them and frees space.
- Notes are readable offline (when opened before); writing notes needs a connection.

Signing out (or signing in as another user) removes local data and files from the device;
the app warns if progress hasn't synced yet.

## Deployment

Serve `dist/` and the Django backend from the **same origin** (e.g. nginx: `/api/`,
`/media/`, `/admin/`, `/static/` to Django, everything else to `dist/` with an
`index.html` fallback), over HTTPS. Serve `sw.js` with `Cache-Control: no-cache`.
