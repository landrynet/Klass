# KLASS — Plateforme SaaS de Gestion Scolaire

> Plateforme multi-établissements pour la gestion numérique des écoles.
> Développée dans le cadre du projet académique — Université Don Bosco de Lubumbashi (UDBL).

## Stack technique

| Composant | Technologie |
|-----------|-------------|
| Backend | Django 5.1 + Django REST Framework |
| Multi-tenant | django-tenants (schéma PostgreSQL par école) |
| Base de données | PostgreSQL 14+ |
| Cache / Broker | Redis 7 |
| Tâches async | Celery 5 + Celery Beat |
| Frontend | Django Templates + HTMX + Alpine.js + Bootstrap 5 |
| PWA | manifest.json + Service Worker |
| Stockage | django-storages (Cloudflare R2 / Backblaze B2) |
| Conteneurs | Docker + Docker Compose |
| Tests | pytest-django |

## Principes d'architecture

- **Pas de Django Admin** — `django.contrib.admin` est entièrement exclu de `INSTALLED_APPS` et des URLs. Toutes les interfaces de gestion sont des dashboards personnalisés.
- **Multi-tenant** — chaque école dispose de son propre schéma PostgreSQL isolé via django-tenants.
- **Routage auth-aware** — la racine `/` redirige intelligemment selon le rôle de l'utilisateur connecté (voir section Rôles).

---

## Démarrage rapide (développement local)

### Prérequis

- Python 3.11+
- PostgreSQL 14+
- Redis 7+

### Option A — Script automatique (recommandé)

```bash
cd klass

# 1. Copier et remplir les variables d'environnement
cp .env.example .env
# Éditez .env avec vos valeurs (SECRET_KEY, DATABASE_URL, REDIS_URL…)

# 2. Créer la base de données PostgreSQL (idempotent)
bash scripts/setup_db.sh

# 3. Lancer le projet complet
bash run.sh
```

`run.sh` effectue automatiquement dans l'ordre :

| Étape | Action |
|-------|--------|
| 1 | Vérification Git (pull si dépôt distant disponible) |
| 2 | Création ou réutilisation du virtualenv Python |
| 3 | Installation des dépendances (`requirements/development.txt`) |
| 4 | Vérification des variables d'environnement obligatoires |
| 5 | Vérification PostgreSQL + test de connexion Django |
| 6 | Vérification Redis |
| 7 | Vérification Celery |
| 8 | Migrations (`migrate_schemas --shared` puis `migrate_schemas`) |
| 9 | Collecte des fichiers statiques |
| 10 | Tests de santé (`manage.py check`) |
| 11 | Démarrage Celery Worker + Beat + serveur Django |

Options disponibles :

```bash
bash run.sh --skip-git      # Ignorer la vérification Git
bash run.sh --skip-celery   # Ne pas démarrer Celery
```

### Option B — Installation manuelle

```bash
cd klass

# Environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Windows : .venv\Scripts\activate
pip install -r requirements/development.txt

# Configuration
cp .env.example .env
# Éditez .env avec vos valeurs

# Base de données
bash scripts/setup_db.sh

# Migrations
python manage.py migrate_schemas --shared
python manage.py migrate_schemas

# Superutilisateur
python manage.py createsuperuser

# Lancer le serveur
python manage.py runserver
```

### Option C — Docker Compose

```bash
cp .env.example .env
# Éditez .env si nécessaire

docker compose up
```

Le service sera accessible sur http://localhost:8000

---

## Variables d'environnement

| Variable | Obligatoire | Description |
|----------|:-----------:|-------------|
| `SECRET_KEY` | ✅ | Clé secrète Django |
| `DATABASE_URL` | ✅ | URL complète PostgreSQL (`postgres://user:pass@host:5432/db`) |
| `REDIS_URL` | ✅ | URL Redis (`redis://localhost:6379/0`) |
| `POSTGRES_DB` | ✅ | Nom de la base |
| `POSTGRES_USER` | ✅ | Utilisateur PostgreSQL |
| `POSTGRES_PASSWORD` | ✅ | Mot de passe PostgreSQL |
| `POSTGRES_HOST` | ✅ | Hôte PostgreSQL |
| `POSTGRES_PORT` | ✅ | Port PostgreSQL (5432) |
| `DJANGO_SETTINGS_MODULE` | — | `config.settings.development` par défaut |
| `KLASS_DOMAIN` | — | Domaine principal (ex : `klass.app`) |
| `USE_EXTERNAL_STORAGE` | — | `False` en développement |
| `SENTRY_DSN` | — | Monitoring erreurs (optionnel) |

Générer une `SECRET_KEY` :
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## Commandes utiles

```bash
# Vérifier la configuration Django
python manage.py check

# Créer les migrations
python manage.py makemigrations

# Vérifier les migrations manquantes
python manage.py makemigrations --check

# Appliquer les migrations (multi-tenant)
python manage.py migrate_schemas --shared   # Schéma public
python manage.py migrate_schemas            # Tous les tenants

# Lancer les tests
pytest

# Lancer Celery worker (développement)
celery -A config.celery worker --loglevel=info

# Lancer Celery beat (planificateur)
celery -A config.celery beat --loglevel=info

# Collecter les fichiers statiques
python manage.py collectstatic --noinput
```

---

## Architecture multi-tenant

Chaque école cliente dispose d'un **schéma PostgreSQL dédié**.

```
Base PostgreSQL "klass"
├── Schéma public (partagé)
│   ├── tenants_school         ← Liste des écoles
│   ├── tenants_domain         ← Sous-domaines
│   ├── accounts_user          ← Utilisateurs globaux (super_admin)
│   └── django_celery_beat_*   ← Planification
│
├── Schéma school_ecole_xyz (école A)
│   ├── school_years_schoolyear
│   ├── academics_*
│   ├── students_*
│   ├── finance_*
│   ├── scheduling_*
│   └── ...
│
└── Schéma school_ecole_abc (école B)
    └── (mêmes tables, données isolées)
```

---

## Modules (8 phases de développement)

| Phase | Module | Statut |
|-------|--------|--------|
| 0 | Socle architectural | ✅ Terminé |
| 1 | Classes, Niveaux, Options & Salles | 🏗️ Architecture prête |
| 2 | Inscription & Dossier Élève | 🏗️ Architecture prête |
| 3 | Personnel Enseignant | 🏗️ Architecture prête |
| 4 | Emploi du Temps | 🏗️ Architecture prête |
| 5 | Paiement Scolaire | 🏗️ Architecture prête |
| 6 | Ressources Pédagogiques | 🏗️ Architecture prête |
| 7 | Portail Parents/Élèves (PWA) | 🏗️ Architecture prête |
| 8 | Gestion des Années Scolaires | 🏗️ Architecture prête |

---

## Rôles

| Rôle | Description | Redirection après login |
|------|-------------|------------------------|
| `super_admin` | Gère les écoles clientes (accès global) | Page super-admin (dashboard à venir) |
| `school_admin` | Directeur d'établissement (accès complet à son école) | `academics:dashboard` |
| `secretary` | Secrétariat (inscriptions) | `academics:dashboard` |
| `accountant` | Comptable (paiements) | `academics:dashboard` |
| `teacher` | Enseignant (emploi du temps, ressources) | `academics:dashboard` |
| `parent` | Portail en lecture (ses enfants) | `portal:dashboard` |
| `student` | Portail en lecture (ses propres données) | `portal:dashboard` |

---

## Documentation

- [Architecture](docs/architecture.md)
- [Base de données](docs/database.md)
- [Multi-tenant](docs/multi-tenancy.md)
- [Permissions](docs/permissions.md)
- [Développement](docs/development.md)
# Klass
