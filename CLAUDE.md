# CLAUDE.md

Django 6.1 REST API backend ("Quant Research Roadmaps") for following time-boxed study roadmaps. A roadmap is a set of **courses** placed on a shared week timeline; the seed data is one 58-week "ML Quant Research Path" made of six courses (one per textbook). The backend is API-only (django-ninja under `/api/`, plus `/admin/` for editing content); the frontend is built separately. The old server-rendered PWA (templates, static, `pwa` app, HTML views) was removed on 2026-11-19 and archived in `legacy-html-frontend.tar.gz`. Git repo (see `.gitignore`: the database, its backups, `media/` uploads and the archive are not tracked).

## Commands

Dependencies are not installed system-wide. The pipenv venv lives at `~/.local/share/virtualenvs/studyplan-OWPpQoLi/` (the shell may have a different project's venv active, which lacks `django_ckeditor_5`). Pipfile pins Python 3.12 and lists `black`.

```bash
python manage.py migrate
python manage.py loaddata fixtures/initial_v16.json   # seed: 1 roadmap, 6 courses, 62 chapters, 217 topics, 39 resources; no users/progress
python manage.py createsuperuser                       # needed to edit content in /admin/
python manage.py runserver                             # API at http://127.0.0.1:8000/api/ (docs: /api/docs)
python manage.py check
python manage.py test                                  # API tests (tests.py / test_api.py per app)
python make_initial.py                                 # regenerates fixtures/initial_v16.json from the Python source of the curriculum
```

Only run `makemigrations` after changing a model. `make_initial.py` is the source of truth for seed content (it asserts week-hour limits and referential integrity); edit it rather than the JSON. Older `fixtures/initial_v1..v13.json` use the pre-course schema and no longer load. Format with `black` (don't run it over `make_initial.py`, which isn't black-formatted).

Config comes from env vars read in [config/settings.py](config/settings.py): `DJANGO_SECRET_KEY`, `DJANGO_DEBUG` (default `1`), `DJANGO_ALLOWED_HOSTS`, `DJANGO_CORS_ALLOWED_ORIGINS` (frontend origins for `/api/`), `DJANGO_JWT_ACCESS_MINUTES` (15), `DJANGO_JWT_REFRESH_DAYS` (30). Database is SQLite at `db.sqlite3` (holds local data). `TIME_ZONE` is `America/New_York`. Rich text fields use `django_ckeditor_5`.

## Architecture

Apps under project package `config/`. Each app with endpoints has `schemas.py` (Ninja `Schema`/`ModelSchema`) and `api.py` (a `Router`); derivation logic lives in `services.py`. Dependency direction: `library` ← `curriculum` ← `roadmaps` ← `progress`; `notes` attaches to all of them generically. There are no HTML views, templates or app static files (only the admin's).

- **[accounts/](accounts/)** – no models. JWT auth for the API (`api.py`: register/login/refresh/logout/me) and `auth.py`: `jwt_auth` (required, the API default) and `optional_auth` (`[jwt_auth, AnonymousAuth()]` for endpoints that also serve signed-out visitors; an invalid token is still 401).
- **[library/](library/)** – `Resource`: any study material (book, paper, problem set, solutions, notes, code, slides, video, other via `kind`). Has an optional uploaded `file` and/or a `url` (`clean()` requires at least one; `href` picks the file first), optional `author` and `thumbnail`. Resources attach to courses, chapters and topics (`resources` M2M on each); there is no separate Link model.
- **[curriculum/](curriculum/)** – content. `Course` (name, rich description, `resources` M2M) → `Chapter` (FK `course`, `week` = week *within the course*, `order` within that week, rich `description`, `deliverable`, `resources` M2M) → `Topic` (`total_time` is estimated **hours**, `order`, `tags` M2M, `resources` M2M). `Tag` has a case-insensitive unique constraint on `Lower("name")`.
- **[roadmaps/](roadmaps/)** – scheduling. `RoadMap` (name, description) → `RoadMapCourse` (`course` PROTECTed, `start_week`, `order`; unique per roadmap+course). A chapter falls on roadmap week `start_week + chapter.week − 1`; courses whose ranges overlap run in parallel and share week sections in the UI.
- **[progress/](progress/)** – per-user state. `UserRoadMap` = the user follows a roadmap (gates checkboxes/progress UI). `UserTopicProgress(user, topic, completed_at)` unique per user+topic: **a row exists only while the topic is completed** (unchecking deletes it).
- **[notes/](notes/)** – per-user rich-text notes via a generic FK on `Course`, `Chapter`, `Topic`, `RoadMap`, `Resource` (allowed targets in `NOTE_TARGETS`). Endpoints call `attach_note_counts(objects, user)` so schemas can expose `note_count`.

### REST API

- [config/api.py](config/api.py) holds the single `NinjaAPI` (`auth=jwt_auth`, docs at `/api/docs` when DEBUG) and mounts each app's router: `/auth`, `/roadmaps`, `/curriculum`, `/library`, `/progress`, `/notes`. It also turns `ninja_extra` `APIException`s (raised by ninja-jwt) into `{"detail": ...}` responses.
- Auth is **only** `Authorization: Bearer <access>` (django-ninja-jwt); the session cookie is ignored by the API (`request.user` is the token user or AnonymousUser). Refresh rotates the refresh token and blacklists the old one (`ninja_jwt.token_blacklist`); logout blacklists it. CORS (`django-cors-headers`) applies to `/api/` only.
- Responses reuse the services: `roadmaps/services.py` (`course_schedule`, `build_outline`, `roadmap_cards`, `roadmap_overview`, `course_player`, snapshots/stats), `library/services.py`, `progress/services.py` (`set_completion`). Shared schema bits in [config/schemas.py](config/schemas.py): `RichHTML` (rich text sanitized with the nh3 allowlist in `notes/richtext.py`; notes use `sanitize_note_html`), `ErrorOut`, `absolute_url` (file/thumbnail URLs are absolute).
- Tests: `config/testing.py` `APITestCase` (fixture data, `get`/`send` with a token for `user`).

### Key design points

- **Nothing derivable is stored.** Roadmap length, week titles, week hours and course week ranges are all computed from chapters/topics (`course_schedule()` and `build_outline()` in [roadmaps/services.py](roadmaps/services.py)).
- **Progress is shared per topic**: completing a topic shows in every roadmap containing its course. All progress numbers come from `roadmap_progress(user, roadmap_ids)` / `course_progress(user, course_ids)` in [progress/models.py](progress/models.py) — don't recompute them elsewhere. The completion JSON returns both (`progress` for the roadmap, `course` for the topic's course).
- `GET /api/roadmaps/{id}` is the overview (`roadmap_overview()`): course schedule with per-course progress and `state` (done/current/upcoming), `finish`, the week-by-week outline (`build_outline()` over the whole roadmap), next topic, totals.
- The course player (`course_player()`): `GET /api/roadmaps/{id}/courses/{course_id}?week=&topic=` returns the current topic, previous/next (within the course) and the course's outline; without `topic` it resumes at the first unfinished topic (of `week`, a roadmap-timeline week). `.../courses/{course_id}/topics/{topic_id}` returns only the topic pane; `/roadmaps/{id}/weeks/{week}` and `/roadmaps/{id}/topics/{topic_id}` resolve the owning course.
- `roadmap_snapshot()` derives next topic, current week, schedule pace (from `UserRoadMap.started_at`) and estimated hours for `GET /api/progress/dashboard` and `/api/progress/overview`. Nothing new is stored.
- Completion is `PUT /api/progress/roadmaps/{rid}/topics/{tid}/completion` `{"completed": bool}`: idempotent, requires a `UserRoadMap` for that roadmap and a topic belonging to it (404 otherwise), returns `completed`, `progress` (roadmap) and `course`. Following is `PUT /api/progress/roadmaps/{rid}/enrollment`.

### URLs ([config/urls.py](config/urls.py))

| Path | Notes |
|---|---|
| `/api/...` | REST API, see [config/api.py](config/api.py) and `/api/docs` (DEBUG) |
| `/admin/` | courses (inline chapters), chapters (inline topics), roadmaps (inline course placements) |
| `/ckeditor5/` | CKEditor uploads for the admin's rich-text fields |
| `/media/` | uploaded files, served by Django only when DEBUG |

## Conventions and gotchas

- API responses are personal: `config.middleware.PrivateAPIResponseMiddleware` marks requests with an `Authorization` header (or an admin session) `Cache-Control: private`. A frontend service worker must not cache `/api/` or `/media/`.
- `course_schedule()` prefetches `course__chapters__topics__{tags,resources}` `course__resources` and `course__chapters__resources`; keep the prefetch when editing to avoid N+1 queries.
- The 2026-11 course migration (`roadmaps/0005_courses_from_roadmaps`) converted each old per-book roadmap into a course; a pre-migration backup is at `db.sqlite3.bak-pre-courses`. `library/0002_book_to_resource` renamed `Book` → `Resource` in place (backup: `db.sqlite3.bak-pre-resources`); it depends on the later curriculum/roadmaps migrations so a fresh database can still resolve `library.book` in older ones. `curriculum/0012_topic_links_to_resources` turned each `Link` into a URL-only Resource (titles/kinds from its `KNOWN` table, mirrored in `make_initial.py`'s `LINK_INFO`) and removed `Link` (backup: `db.sqlite3.bak-pre-link-resources`).
- `media/books/` files match the stored `Resource.file` paths except two that are missing: `hyndman_athanasopoulos_fpp3.pdf` and `strang_introduction_to_linear_algebra_5e.pdf` (their links 404 until uploaded). `Introduction_to_Probability_2nd_Edition_2008_Athena_Scientific.pdf` (Bertsekas & Tsitsiklis) and `wasserman_all_of_statistics_qC57523.pdf.pdf` (byte-identical duplicate) aren't referenced by any resource.
- Seed fixtures use fixed PKs; rerunning `loaddata` overwrites those rows (and admin edits to them).
- `SECRET_KEY`/SQLite defaults are dev-only; set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CORS_ALLOWED_ORIGINS`, a real database and HTTPS before deploying (the HTTPS/proxy env vars are documented in settings.py).
