from datetime import timedelta
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-change-me-before-deployment")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "ninja_jwt",
    "ninja_jwt.token_blacklist",
    "django_ckeditor_5",
    "accounts",
    "curriculum",
    "library",
    "roadmaps",
    "progress",
    "notes",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "config.middleware.PrivateAPIResponseMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]
WSGI_APPLICATION = "config.wsgi.application"
DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}
}
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/New_York"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"  # collectstatic target for production
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
FIXTURE_DIRS = [BASE_DIR / "fixtures"]

CKEDITOR_5_CONFIGS = {
    "default": {
        "toolbar": [
            "heading",
            "|",
            "bold",
            "italic",
            "link",
            "|",
            "bulletedList",
            "numberedList",
            "blockQuote",
            "code",
            "codeBlock",
            "|",
            "undo",
            "redo",
        ],
    },
}

# REST API (django-ninja, mounted at /api/, see config/api.py). Clients authenticate
# with a JWT access token (`Authorization: Bearer <access>`) from POST /api/auth/login
# and renew it with the refresh token at POST /api/auth/refresh. Refresh tokens
# rotate and the old one is blacklisted; logout blacklists the current one.
NINJA_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=int(os.environ.get("DJANGO_JWT_ACCESS_MINUTES", "15"))
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=int(os.environ.get("DJANGO_JWT_REFRESH_DAYS", "30"))
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "SIGNING_KEY": SECRET_KEY,
}

# A separately hosted frontend calls the API cross-origin: list its origin(s) in
# DJANGO_CORS_ALLOWED_ORIGINS (comma-separated, e.g. http://localhost:8083). Not
# needed when the frontend proxies /api and /media (the Vite dev server does).
# Bearer tokens are not cookies, so credentials are not allowed cross-origin.
CORS_ALLOWED_ORIGINS = [
    o for o in os.environ.get("DJANGO_CORS_ALLOWED_ORIGINS", "").split(",") if o
]
CORS_URLS_REGEX = r"^/(api|media)/.*$"  # media: offline file downloads

# HTTPS / proxy settings. Behind a TLS-terminating proxy or tunnel (nginx, Caddy,
# ngrok, Cloudflare Tunnel), set DJANGO_BEHIND_PROXY=1 so Django trusts
# X-Forwarded-Proto, and list the public origin(s) in DJANGO_CSRF_TRUSTED_ORIGINS
# (comma-separated, e.g. https://abc.ngrok.app) so the admin's forms are accepted.
CSRF_TRUSTED_ORIGINS = [
    o for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o
]
if os.environ.get("DJANGO_BEHIND_PROXY") == "1":
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = os.environ.get("DJANGO_SSL_REDIRECT", "1") == "1"
    SECURE_CONTENT_TYPE_NOSNIFF = True
    # Opt in once the whole site is HTTPS-only (hard to undo; see Django docs).
    SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_HSTS_SECONDS", "0"))
