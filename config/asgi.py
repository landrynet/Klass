"""
Configuration ASGI pour KLASS.
Point d'entrée pour les serveurs ASGI (Daphne, Uvicorn).
Préparé pour les WebSockets (notifications temps réel futures).
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

application = get_asgi_application()
