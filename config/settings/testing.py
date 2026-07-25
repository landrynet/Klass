"""
Settings pour les tests de KLASS.
Base de données de test séparée, Celery synchrone, Debug Toolbar désactivé.
"""
from .base import *  # noqa

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
DEBUG = False

# Les tests des vues publiques et du Super Admin utilisent `testserver`
# sans sous-domaine d'école. Comme en développement, laisser
# django-tenants servir le schéma public dans ce cas.
SHOW_PUBLIC_IF_NO_TENANT_FOUND = True

# Désactiver Debug Toolbar (incompatible avec les tests)
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != "debug_toolbar"]  # noqa
MIDDLEWARE = [m for m in MIDDLEWARE if "debug_toolbar" not in m.lower()]  # noqa

# Base de données de test séparée
DATABASES["default"]["TEST"] = {  # noqa
    "NAME": "klass_test",
}

# ---------------------------------------------------------------------------
# Celery — synchrone pour les tests (pas besoin d'un worker réel)
# ---------------------------------------------------------------------------
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# ---------------------------------------------------------------------------
# Stockage
# ---------------------------------------------------------------------------
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
USE_EXTERNAL_STORAGE = False

# ---------------------------------------------------------------------------
# Sécurité allégée pour les tests
# ---------------------------------------------------------------------------
SECRET_KEY = "test-insecure-key-not-for-production-klass-phase1"
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",  # Rapide pour les tests
]

# ---------------------------------------------------------------------------
# Logging minimal en test
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "null": {"class": "logging.NullHandler"},
    },
    "root": {
        "handlers": ["null"],
        "level": "CRITICAL",
    },
}
