"""
Settings de base pour KLASS — partagés par tous les environnements.
Ne jamais inclure de secrets ici. Utiliser .env via django-environ.
"""
import os
import environ
from pathlib import Path

from config.tenant_config import SHARED_APPS, TENANT_APPS, TENANT_MODEL, TENANT_DOMAIN_MODEL

# ---------------------------------------------------------------------------
# Chemins
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent
APPS_DIR = BASE_DIR / "apps"

# ---------------------------------------------------------------------------
# Environnement
# ---------------------------------------------------------------------------
env = environ.Env(
    DEBUG=(bool, False),
    SECRET_KEY=(str, "changeme-insecure-key"),
    ALLOWED_HOSTS=(list, ["*"]),
    DATABASE_URL=(str, "postgres://klass:klass@localhost:5432/klass"),
    REDIS_URL=(str, "redis://localhost:6379/0"),
)

# Charger le fichier .env si présent
environ.Env.read_env(BASE_DIR / ".env")

# ---------------------------------------------------------------------------
# Sécurité de base
# ---------------------------------------------------------------------------
SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# ---------------------------------------------------------------------------
# Multi-tenant (django-tenants)
# ---------------------------------------------------------------------------
INSTALLED_APPS = list(SHARED_APPS) + [app for app in TENANT_APPS if app not in SHARED_APPS]

TENANT_MODEL = TENANT_MODEL
TENANT_DOMAIN_MODEL = TENANT_DOMAIN_MODEL

DATABASE_ROUTERS = ["django_tenants.routers.TenantSyncRouter"]

# ---------------------------------------------------------------------------
# Middleware
# La TenantMainMiddleware DOIT être en premier position
# ---------------------------------------------------------------------------
MIDDLEWARE = [
    "django_tenants.middleware.main.TenantMainMiddleware",  # Multi-tenant — PREMIER
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.TenantContextMiddleware",    # Contexte école courant
    "apps.core.middleware.MustChangePasswordMiddleware",  # Changement mot de passe obligatoire
    "apps.core.middleware.SetupRequiredMiddleware",    # Configuration initiale obligatoire
]

ROOT_URLCONF = "config.urls"

# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.school_context",  # Contexte école
                "apps.core.context_processors.user_role_context",  # Contexte rôle
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------------------
# Base de données (PostgreSQL multi-tenant)
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        **env.db("DATABASE_URL"),
        "ENGINE": "django_tenants.postgresql_backend",  # Backend multi-tenant OBLIGATOIRE
    }
}

# ---------------------------------------------------------------------------
# Modèle utilisateur personnalisé
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"

# ---------------------------------------------------------------------------
# Validation des mots de passe
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Africa/Lubumbashi"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Fichiers statiques et media
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Sessions et sécurité des cookies
# ---------------------------------------------------------------------------
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = False  # Accessible JS pour HTMX
CSRF_COOKIE_SAMESITE = "Lax"

# ---------------------------------------------------------------------------
# Redis et Celery
# ---------------------------------------------------------------------------
REDIS_URL = env("REDIS_URL")

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_TASK_ALWAYS_EAGER = False  # Surcharger à True dans testing

# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@klass.app")
SERVER_EMAIL = env("SERVER_EMAIL", default="server@klass.app")

# ---------------------------------------------------------------------------
# Stockage externe (Cloudflare R2 / Backblaze B2)
# ---------------------------------------------------------------------------
USE_EXTERNAL_STORAGE = env.bool("USE_EXTERNAL_STORAGE", default=False)

if USE_EXTERNAL_STORAGE:
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    AWS_ACCESS_KEY_ID = env("STORAGE_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = env("STORAGE_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = env("STORAGE_BUCKET_NAME")
    AWS_S3_ENDPOINT_URL = env("STORAGE_ENDPOINT_URL")
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = "private"

# ---------------------------------------------------------------------------
# Sentry
# ---------------------------------------------------------------------------
SENTRY_DSN = env("SENTRY_DSN", default="")

if SENTRY_DSN:
    import sentry_sdk
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=0.1,
        environment=env("ENVIRONMENT", default="production"),
    )

# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------
LOGIN_URL = "/auth/login/"
LOGIN_REDIRECT_URL = "/portal/"
LOGOUT_REDIRECT_URL = "/auth/login/"

# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------
from django.contrib.messages import constants as messages

MESSAGE_TAGS = {
    messages.DEBUG: "debug",
    messages.INFO: "info",
    messages.SUCCESS: "success",
    messages.WARNING: "warning",
    messages.ERROR: "danger",
}

# ---------------------------------------------------------------------------
# CORS (API REST)
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
CORS_ALLOW_CREDENTIALS = True
