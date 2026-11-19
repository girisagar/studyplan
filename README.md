# Quant Research Roadmaps — API

A Django 6.1 REST API (django-ninja) for following time-boxed study roadmaps: a roadmap places
courses on a shared week timeline; users follow roadmaps, check off topics and keep notes.
Content is edited in the Django admin. The frontend lives in a separate project.

## Get started

Requires Python 3.12.

```bash
pipenv install                     # or: pip install -r requirements.txt
python manage.py migrate
python manage.py loaddata fixtures/initial_v16.json
python manage.py createsuperuser   # to edit content at /admin/
python manage.py runserver
```

- API: http://127.0.0.1:8000/api/ — interactive docs at `/api/docs` (when `DJANGO_DEBUG=1`)
- Admin: http://127.0.0.1:8000/admin/

## Authentication

JWT bearer tokens (django-ninja-jwt):

1. `POST /api/auth/register` or `POST /api/auth/login` → `{access, refresh, user}`
2. Send `Authorization: Bearer <access>` on requests.
3. When the access token expires (401), `POST /api/auth/refresh` with `{refresh}` → new pair
   (the old refresh token stops working).
4. `POST /api/auth/logout` with `{refresh}` revokes it.

Browsing roadmaps, courses and the library works without a token; progress, notes and the
dashboard need one.

## Configuration (environment variables)

| Variable | Default | Purpose |
|---|---|---|
| `DJANGO_SECRET_KEY` | dev key | also signs JWTs |
| `DJANGO_DEBUG` | `1` | debug mode, `/api/docs`, media serving |
| `DJANGO_ALLOWED_HOSTS` | `*` | comma-separated |
| `DJANGO_CORS_ALLOWED_ORIGINS` | – | frontend origin(s), e.g. `http://localhost:3000` |
| `DJANGO_JWT_ACCESS_MINUTES` | `15` | access token lifetime |
| `DJANGO_JWT_REFRESH_DAYS` | `30` | refresh token lifetime |

SQLite and the default secret key are for local development only.
