# Quant Research Roadmaps

Follow time-boxed study roadmaps: courses placed on a shared week timeline, topic check-off,
progress and notes.

| Part | What | Docs |
|---|---|---|
| [`backend/`](backend/) | Django REST API (django-ninja, JWT) + admin | [backend/README.md](backend/README.md) |
| [`frontend/`](frontend/) | Offline-first PWA (React, TypeScript, Vite) | [frontend/README.md](frontend/README.md) |

Quick start (backend):

```bash
cd backend
pipenv install
pipenv run python manage.py migrate
pipenv run python manage.py loaddata fixtures/initial_v16.json
pipenv run python manage.py runserver   # API: http://127.0.0.1:8000/api/docs
```

Frontend (in another terminal):

```bash
cd frontend
npm install
npm run dev                              # http://localhost:8083 (all interfaces)
```
