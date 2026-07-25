"""
Configuration WSGI pour KLASS.
Point d'entrée pour les serveurs WSGI (Gunicorn en production).
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

application = get_wsgi_application()
