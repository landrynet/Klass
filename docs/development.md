# Guide de développement KLASS

## Environnement de développement

### Prérequis

- Python 3.13+
- PostgreSQL 14+
- Redis 7+
- Docker (optionnel mais recommandé)

### Installation

```bash
cd klass
python -m venv .venv
source .venv/bin/activate
pip install -r requirements/development.txt
cp .env.example .env
# Éditez .env
python manage.py migrate_schemas --shared
python manage.py migrate_schemas
python manage.py createsuperuser
python manage.py runserver
```

## Lancer les tests

```bash
# Tous les tests
pytest

# Tests d'un module spécifique
pytest tests/test_accounts.py -v

# Avec couverture
pytest --cov=apps --cov-report=html
```

## Ajouter un nouveau module

1. Créer l'app Django dans `apps/`:
   ```bash
   cd apps && python -m django startapp mon_module && cd ..
   ```

2. Créer `apps/mon_module/apps.py` avec `AppConfig`

3. Ajouter dans `config/tenant_config.py`:
   ```python
   TENANT_APPS = [..., "apps.mon_module"]
   ```

4. Créer les modèles (hériter de `TenantAwareModel`)

5. Créer les migrations:
   ```bash
   python manage.py makemigrations mon_module
   python manage.py migrate_schemas
   ```

6. Ajouter les URLs dans `config/urls.py`

## Celery en développement

```bash
# Terminal 1 — Worker
celery -A config.celery worker --loglevel=info

# Terminal 2 — Beat (planificateur)
celery -A config.celery beat --loglevel=info

# Tester une tâche
python manage.py shell
>>> from config.celery import debug_task
>>> debug_task.delay()
```

## Créer une école (développement)

```python
python manage.py shell
>>> from apps.tenants.services import create_school_with_tenant
>>> school, admin, pwd = create_school_with_tenant(
...     name="École Test",
...     email="admin@ecole-test.com",
... )
>>> print(f"Admin: {admin.email} / Mot de passe: {pwd}")
```
