# CLAUDE.md (frontend)

Offline-first PWA for the Django API in `../backend`. React 19 + TypeScript 7 (strict by default) + Vite 8, `react-router` 8 (data router in `src/App.tsx`), `vite-plugin-pwa` with `strategies: 'injectManifest'` (`src/sw.ts`), `idb`, `pdfjs-dist` 6. No UI framework: styles are in `src/styles.css` (theme tokens on `[data-theme]`, set before paint in `index.html`; light/dark/system in Profile). Inline SVG icons in `src/components/Icon.tsx`.

## Commands

```bash
npm install          # postinstall copies PDF.js assets to public/pdfjs (git-ignored)
npm run dev          # 0.0.0.0:8083, proxies /api and /media to BACKEND_URL (default 127.0.0.1:8000)
npm run typecheck    # tsc -b (app, sw and node configs)
npm run lint         # oxlint
npm run build && npm run preview   # 0.0.0.0:8083 too, service worker active
npm run e2e          # Playwright offline test against preview; creates progress for E2E_USER
```

`openapi-typescript` doesn't support TS 7 yet, so `src/api/types.ts` is hand-written from `backend/*/schemas.py` — update it with backend schema changes.

## Offline architecture (keep these invariants)

- **API cache** ([src/offline/cache.ts](src/offline/cache.ts)): every GET goes through `useApi(path)` / `fetchAndCache(path)`; responses are stored in IndexedDB (`cache` store, key = API path) and mirrored in memory. `startOffline()` hydrates everything before the first render, so reads are synchronous. The service worker never caches `/api/` (data is per user).
- **Sync** ([src/offline/sync.ts](src/offline/sync.ts)): `requestSync(full)` pushes the outbox, then `pullAll()` refreshes the offline set (`/roadmaps` + each detail, `/curriculum/courses/{id}` for every scheduled course, `/library/resources` + each detail, `/library/kinds`, and when signed in `/auth/me`, `/progress/enrollments`, `/progress/completions`) and prunes deleted ones. Triggers: start, `online`, visibility, outbox changes, 60 s retry, sign-in.
- **Progress** ([src/offline/progress.ts](src/offline/progress.ts)): local state = server `/progress/completions` + `/progress/enrollments` with the IndexedDB `outbox` applied (`computeLocalProgress`). Never mutate progress via direct API calls from UI — use `setTopicCompleted` / `followRoadmap` (they coalesce per topic and never cancel the op in flight). Ops carry the client time (`completed_at`/`started_at`); 4xx rejections are dropped with a notice, network/5xx/401 keep them.
- **Derived views** ([src/domain/derive.ts](src/domain/derive.ts)): order/weeks come from the server outline (`RoadMapDetail.sections`); completion, progress, course state, next topic, pace and stats are recomputed locally. Don't use the server's `progress`/`completed`/`next_item`/dashboard fields in UI (stale offline).
- **Files** ([src/offline/files.ts](src/offline/files.ts)): bodies in Cache Storage `FILES_CACHE` (key = absolute file URL), metadata in IndexedDB `files`. `src/sw.ts` answers `/media/` from that cache, else network without storing. Thumbnails and PDF.js cmaps are runtime-cached.
- **Auth** ([src/auth](src/auth)): JWTs + user in localStorage (`studyplan.session`); `api()` refreshes once on 401 (shared promise). A rejected refresh marks the session `expired` (data stays readable, sync asks to sign in). `studyplan.owner` = user id whose data is stored; another user's sign-in or sign-out calls `wipeLocalData()`.

## Conventions

- Rich text from the API is server-sanitized; render it only through `<Rich html>`.
- Player URL: `/roadmaps/:id/courses/:courseId?topic=&week=` (`playerPath()` in `src/domain/paths.ts`); the player writes the resolved `topic` into the URL.
- Keep component files exporting only components (fast refresh); shared functions go in `src/domain`, `src/hooks`, or plain `.ts` modules (e.g. `components/toast.ts`).
- Effects always use a block body (`useEffect(() => { ... })`): React treats any returned value as the cleanup, and e.g. `window.scrollTo()` returns a Promise in newer browsers, which crashed route changes.
- Pending progress changes render through `<PendingBadge topicId>` (`src/offline/pending.ts`): nothing while a change is on its way; "not synced" only after a sync attempt that included it failed (`SyncStatus.unsentBefore`: offline, server unreachable/error, sign-in needed). No spinners.
- Form fields keep a font size of at least 16px (`input, textarea, select` in `styles.css`); smaller text makes iOS Safari zoom the page on focus. Never disable zoom in the viewport meta.
