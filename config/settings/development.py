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

# Domaine de fallback pour le tenant en développement
# Permet d'accéder à localhost:8000 sans sous-domaine configuré
SHOW_PUBLIC_IF_NO_TENANT_FOUND = True

# ---------------------------------------------------------------------------
# Base de données locale
# ---------------------------------------------------------------------------
# Utilise DATABASE_URL depuis .env ou valeur par défaut
DATABASES["default"]["HOST"] = env("POSTGRES_HOST", default="localhost")

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
