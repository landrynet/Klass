"""
Configuration multi-tenant pour KLASS.
Définit les apps partagées (public schema) et les apps tenant (schema par école).

Architecture:
  - SHARED_APPS  → tables dans le schéma 'public' (global à toutes les écoles)
  - TENANT_APPS  → tables dupliquées dans chaque schéma école (isolation stricte)
"""

# Apps dans le schéma public (disponibles globalement)
SHARED_APPS = [
    "django_tenants",          # Obligatoire : doit être en premier
    "apps.tenants",            # Modèles School & Domain
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.core",               # Utilitaires partagés
    "apps.accounts",           # Modèle utilisateur partagé (super_admin inclus)
    # Third-party shared
    "django_celery_beat",
]

# Apps dans chaque schéma tenant (isolées par école)
TENANT_APPS = [
    "django.contrib.contenttypes",  # Requis par django-tenants dans chaque schéma
    "apps.school_years",       # Années scolaires
    "apps.academics",          # Niveaux, options, classes, salles, matières
    "apps.students",           # Élèves, dossiers, parents
    "apps.teachers",           # Personnel enseignant
    "apps.finance",            # Paiements, frais, reçus
    "apps.scheduling",         # Emploi du temps
    "apps.resources",          # Ressources pédagogiques
    "apps.portal",             # Portail parents/élèves
    "apps.communications",     # Messages, annonces
    "apps.notifications",      # Alertes, push, SMS, email
]

# Modèles django-tenants
TENANT_MODEL = "tenants.School"
TENANT_DOMAIN_MODEL = "tenants.Domain"
