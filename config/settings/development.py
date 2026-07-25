"""
Settings de développement pour KLASS.
Active le debug, les outils de développement et simplifie la configuration.
"""
from .base import *  # noqa

# ---------------------------------------------------------------------------
# Développement
# ---------------------------------------------------------------------------
DEBUG = True
ALLOWED_HOSTS = ["*", "localhost", "127.0.0.1", ".localhost"]

# Replit preview support — autoriser tous les sous-domaines replit.dev en développement
import os as _os_dev
_replit_dev = _os_dev.environ.get("REPLIT_DEV_DOMAIN", "")
CSRF_TRUSTED_ORIGINS = [
    "https://*.replit.dev",
    "https://*.repl.co",
    "http://localhost:5000",
    "http://127.0.0.1:5000",
]
if _replit_dev:
    CSRF_TRUSTED_ORIGINS.append(f"https://{_replit_dev}")

# Domaine de fallback pour le tenant en développement
# Permet d'accéder à localhost:8000 sans sous-domaine configuré
SHOW_PUBLIC_IF_NO_TENANT_FOUND = True

# ---------------------------------------------------------------------------
# Base de données locale
# ---------------------------------------------------------------------------
# Ne surcharger HOST que si POSTGRES_HOST est explicitement défini.
# Si DATABASE_URL est utilisé (cas Replit), le HOST vient déjà du URL.
import os as _os
if _postgres_host := _os.environ.get("POSTGRES_HOST"):
    DATABASES["default"]["HOST"] = _postgres_host

# ---------------------------------------------------------------------------
# Email — console en développement
# ---------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ---------------------------------------------------------------------------
# Debug Toolbar
# ---------------------------------------------------------------------------
INSTALLED_APPS += ["debug_toolbar"]  # noqa

MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa

INTERNAL_IPS = ["127.0.0.1", "localhost"]

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG,
}

# ---------------------------------------------------------------------------
# Celery — synchrone en développement (tâches exécutées immédiatement)
# ---------------------------------------------------------------------------
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{levelname}] {asctime} {module} — {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django.db.backends": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "apps": {"handlers": ["console"], "level": "DEBUG", "propagate": False},
        "celery": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
