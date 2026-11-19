"""The project's single NinjaAPI instance; each app contributes a Router from
its own api.py. Mounted at /api/ in config/urls.py (OpenAPI docs: /api/docs)."""

from django.conf import settings
from ninja import NinjaAPI
from ninja_extra.exceptions import APIException

from accounts.api import router as accounts_router
from accounts.auth import jwt_auth
from curriculum.api import router as curriculum_router
from library.api import router as library_router
from notes.api import router as notes_router
from progress.api import router as progress_router
from roadmaps.api import router as roadmaps_router

api = NinjaAPI(
    title="Quant Research Roadmaps API",
    version="1.0.0",
    description="Roadmaps, courses, progress, library and notes. Authenticate "
    "with `Authorization: Bearer <access token>` from `POST /api/auth/login`.",
    auth=jwt_auth,
    urls_namespace="api",
    docs_url="/docs" if settings.DEBUG else None,
)

api.add_router("/auth", accounts_router)
api.add_router("/roadmaps", roadmaps_router)
api.add_router("/curriculum", curriculum_router)
api.add_router("/library", library_router)
api.add_router("/progress", progress_router)
api.add_router("/notes", notes_router)


@api.exception_handler(APIException)
def ninja_extra_error(request, exc):
    """ninja-jwt raises django-ninja-extra exceptions (e.g. an invalid or expired
    token); answer them with their status and a `detail` like other API errors."""
    detail = exc.detail
    if isinstance(detail, dict) and "detail" in detail:
        detail = detail["detail"]
    return api.create_response(request, {"detail": str(detail)}, status=exc.status_code)
