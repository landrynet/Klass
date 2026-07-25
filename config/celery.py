"""
Configuration Celery pour KLASS.
Gère les tâches asynchrones (reçus PDF, notifications, email, SMS)
et les tâches planifiées (Celery Beat).
"""
import os
from celery import Celery
from celery.utils.log import get_task_logger

# Définir le module de settings par défaut
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("klass")

# Charger la configuration depuis les settings Django sous le namespace CELERY_
app.config_from_object("django.conf:settings", namespace="CELERY")

# Découvrir automatiquement les tâches dans tous les modules tasks.py des apps installées
app.autodiscover_tasks()

logger = get_task_logger(__name__)


@app.task(bind=True, name="klass.tasks.debug_task")
def debug_task(self):
    """Tâche de test pour vérifier que Celery fonctionne correctement."""
    logger.info("Celery fonctionne correctement. Task ID: %s", self.request.id)
    return {"status": "ok", "task_id": str(self.request.id)}
