# Architecture KLASS

## Vue d'ensemble

KLASS est une plateforme SaaS Django multi-établissements.
L'architecture sépare clairement les responsabilités par module métier.

## Structure du projet

```
klass/
├── config/                 # Configuration Django
│   ├── settings/
│   │   ├── base.py        # Settings partagés (tous les environnements)
│   │   ├── development.py # Dev (DEBUG=True, emails console, debug toolbar)
│   │   ├── production.py  # Prod (HTTPS, WhiteNoise, logs structurés)
│   │   └── testing.py     # Tests (DB de test, Celery synchrone)
│   ├── urls.py            # Routing principal
│   ├── celery.py          # Configuration Celery
│   └── tenant_config.py   # SHARED_APPS / TENANT_APPS
│
├── apps/
│   ├── core/              # Utilitaires partagés (modèles abstraits, permissions)
│   ├── tenants/           # School + Domain (TenantMixin, DomainMixin)
│   ├── accounts/          # Modèle User personnalisé (AUTH_USER_MODEL)
│   ├── school_years/      # Années scolaires (Module 8)
│   ├── academics/         # Niveaux, options, classes, salles, matières (Module 6)
│   ├── students/          # Élèves, inscriptions, parents (Module 1)
│   ├── teachers/          # Enseignants, qualifications, disponibilités (Module 4)
│   ├── finance/           # Frais, paiements, reçus (Module 2)
│   ├── scheduling/        # Emploi du temps, créneaux (Module 3)
│   ├── resources/         # Ressources pédagogiques (Module 5)
│   ├── portal/            # Portail PWA parents/élèves (Module 7)
│   ├── communications/    # Messages et annonces
│   └── notifications/     # Alertes email, SMS, push
│
├── templates/             # Templates Django (base.html + par module)
├── static/               # CSS, JS, PWA assets
├── tests/                # Tests globaux du socle
├── scripts/              # Scripts utilitaires (seed, migrations)
└── docs/                 # Documentation
```

## Flux de données

```
Navigateur → Middleware TenantMain → Django Router → Vue → Modèle (schéma tenant)
```

## Services asynchrones

```
Django → Celery Worker → Redis → Résultats
         ↑
Celery Beat (planificateur)
```
