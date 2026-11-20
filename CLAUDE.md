# CLAUDE.md

Monorepo for "Quant Research Roadmaps", an app for following time-boxed study roadmaps.

- **[backend/](backend/)**: Django 6.1 REST API (django-ninja, JWT auth) plus the Django admin. Read [backend/CLAUDE.md](backend/CLAUDE.md) before working there, and run its commands from `backend/`.
- **[frontend/](frontend/)**: offline-first PWA (React, TypeScript, Vite, vite-plugin-pwa). Read [frontend/CLAUDE.md](frontend/CLAUDE.md) before working there, and run its commands from `frontend/`.

The frontend talks to the backend only over HTTP with `Authorization: Bearer <access token>`. In development the Vite server proxies `/api` and `/media` to Django (same origin, no CORS needed); in production serve both from one origin. Backend schema changes must be mirrored in `frontend/src/api/types.ts`. The API schema is at `/api/openapi.json` (docs at `/api/docs` when DEBUG).

Git: the root `.gitignore` covers both parts. The database, its backups, `backend/media/` uploads and the legacy archive are not tracked.

## Running on this machine (systemd user services)

- `studyplan-backend.service`: Django `runserver 127.0.0.1:8000` from `backend/` (venv `backend-nIC80V6-`).
- `studyplan.service`: `npm run build` then `vite preview` on `0.0.0.0:8083` from `frontend/`, proxying `/api`, `/media`, `/admin`, `/static`, `/ckeditor5` to the backend (so the admin is at `:8083/admin`). Pulls in the backend service. Its `PATH` pins the nvm Node (`v24.14.0`); update it after switching Node versions.
- Units live in `~/.config/systemd/user/`. After code changes: `systemctl --user restart studyplan` (rebuilds the frontend; the backend dev server autoreloads). Logs: `journalctl --user -u studyplan -u studyplan-backend -f`.
