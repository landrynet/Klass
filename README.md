# KLASS — Plateforme SaaS de Gestion Scolaire

> Plateforme multi-établissements pour la gestion numérique des écoles.
> Développée dans le cadre du projet académique — Université Don Bosco de Lubumbashi (UDBL).

## Stack technique

| Composant | Technologie |
|-----------|-------------|
| Backend | Django 5.1 + Django REST Framework |
| Multi-tenant | django-tenants (schéma PostgreSQL par école) |
| Base de données | PostgreSQL 14+ |
| Cache / Broker | Redis 7 (optionnel en développement) |
| Tâches async | Celery 5 + Celery Beat |
| Frontend | Django Templates + HTMX + Alpine.js + Bootstrap 5 |
| PWA | manifest.json + Service Worker |
| Stockage | django-storages (Cloudflare R2 / Backblaze B2) |
| Conteneurs | Docker + Docker Compose |
| Tests | pytest-django |

## Principes d'architecture

- **Pas de Django Admin** — `django.contrib.admin` est entièrement exclu de `INSTALLED_APPS` et des URLs. Toutes les interfaces de gestion sont des dashboards personnalisés.
- **Multi-tenant** — chaque école dispose de son propre schéma PostgreSQL isolé via django-tenants.
- **Routage auth-aware** — la racine `/` redirige intelligemment selon le rôle de l'utilisateur connecté.
- **FK User → School** — chaque utilisateur école est lié directement à son établissement via une FK (isolation applicative + SQL).

---

## État d'avancement du projet

### Phase 3.1 — Inscriptions et affectation des élèves aux classes
**Statut : ✅ TERMINÉE, STABILISÉE ET VALIDÉE**

Documentation : `docs/modules/phase-3-1-inscriptions.md`

**Fonctionnalités implémentées :**

- ✅ Modèle `StudentEnrollment` complet (élève → année scolaire → classe)
- ✅ Statuts d'inscription : En attente / Active / Terminée / Annulée
- ✅ Règle métier : une seule inscription active par élève/année (validation backend)
- ✅ Historique scolaire multi-années préservé (suppression de unique_together)
- ✅ Changement de classe tracé (ancienne inscription → Terminée, nouvelle créée)
- ✅ Liste des inscriptions avec filtres (année, statut, classe, recherche)
- ✅ Vue par classe (tous les élèves inscrits, taux de remplissage)
- ✅ Fiche élève enrichie (inscription active + historique complet)
- ✅ API JSON : classes dynamiques par année + recherche élève (pour HTMX)
- ✅ Isolation multi-tenant complète (schema_context sur toutes les requêtes)
- ✅ Permissions backend (school_admin écriture, staff lecture)
- ✅ Seed data Phase 3.1 idempotent (3 élèves, 4 inscriptions dont historique)
- ✅ 155 tests — 0 échec (Phases 1, 2.0, 2.1, 3.0, 3.1 + régression)
- ✅ Sidebar mise à jour (lien Inscriptions)

---

### Phase 2.1 — Classes et salles
**Statut : ✅ TERMINÉE, STABILISÉE ET VALIDÉE**

Documentation : `docs/modules/phase-2-1-classes-et-salles.md`

**Fonctionnalités implémentées :**

- ✅ Gestion complète des salles (CRUD, types, capacité, disponibilité, archivage)
- ✅ Gestion complète des classes (CRUD, activation/désactivation, archivage)
- ✅ Association Classe → Salle (FK nullable, vérifiée dans le même schéma tenant)
- ✅ Statuts : Active / Inactive / Archivée (classes) · Disponible / Indisponible / Archivée (salles)
- ✅ Filtres multi-niveaux : année → niveau → option → statut + recherche texte
- ✅ Isolation multi-tenant complète (schema_context sur toutes les requêtes)
- ✅ Permissions backend (school_admin écriture, staff lecture)
- ✅ Validations serveur (unicité, relations inter-école bloquées, archivage protégé)
- ✅ Données de test Phase 2.1 (seed_data.py idempotent — 5 salles, 4 classes)
- ✅ 143 tests — 0 échec (Phase 1, 2.0, 2.1 + régression)
- ✅ Sidebar mise à jour (liens Classes et Salles)

---

### Phase 2.0 — Fondations de la structure académique
**Statut : ✅ TERMINÉE, STABILISÉE ET VALIDÉE**

Documentation : `docs/modules/phase-2-0-fondations-structure-academique.md`

**Fonctionnalités implémentées :**

- ✅ Gestion complète des années scolaires (CRUD + cycle de vie : Planifiée → Active → Terminée → Archivée)
- ✅ Gestion des niveaux scolaires (CRUD, ordre configurable, activation/désactivation)
- ✅ Gestion des options / filières (CRUD, activation/désactivation)
- ✅ Isolation tenant complète (schema_context sur toutes les requêtes)
- ✅ Permissions backend (school_admin pour écriture, staff pour lecture)
- ✅ Validations serveur (unicité, relations invalides, isolation inter-école)
- ✅ Interface responsive (Bootstrap 5, badges de statut, actions contextuelles)
- ✅ Données de test Phase 2.0 (seed_data.py idempotent)
- ✅ Tests unitaires (logique, modèles, formulaires, isolation)
- ✅ Compatibilité Phase 1 préservée (assistant de configuration, années initiales)

---

### Phase 3.0 — Élèves, parents et matricules
**Statut : ✅ TERMINÉE, STABILISÉE ET VALIDÉE**

Documentation : `docs/modules/phase-3-0-eleves-parents-matricules.md`

- ✅ Dossiers élèves et statuts
- ✅ Parents / tuteurs et association à plusieurs élèves
- ✅ Parent principal obligatoire à la création d'un élève
- ✅ Matricules automatiques, uniques et stables
- ✅ Format de matricule configurable par école
- ✅ Recherche, filtres, consultation et interfaces personnalisées
- ✅ Isolation tenant et permissions backend

---

### Phase 0 — Socle architectural
**Statut : ✅ TERMINÉE ET VALIDÉE**

- Architecture multi-tenant (django-tenants)
- Modèle User personnalisé avec rôles
- Modèles School et Domain (TenantMixin)
- Services de création de tenant
- Middleware TenantContextMiddleware
- Système de rôles et permissions
- Templates de base (Bootstrap 5 + HTMX + Alpine.js)

### Phase 1 — Fondation de l'école
**Statut : ✅ TERMINÉE ET VALIDÉE**

Documentation : `docs/modules/phase-1-fondation-ecole.md`

**Fonctionnalités implémentées :**

- ✅ Interface Super Admin personnalisée (dashboard, liste des écoles, création)
- ✅ Formulaire de création d'école avec validation complète
- ✅ Création du tenant PostgreSQL (schéma isolé par école)
- ✅ Création du domaine principal (`slug.klass.app`)
- ✅ Création automatique de l'Admin École avec FK `school`
- ✅ Génération de mot de passe temporaire sécurisé
- ✅ Changement obligatoire du mot de passe à la première connexion
- ✅ Assistant de configuration initiale en 3 étapes :
  - Étape 1 : Informations de l'école (nom, logo, adresse, contact)
  - Étape 2 : Année scolaire initiale
  - Étape 3 : Confirmation et activation
- ✅ Middleware `SetupRequiredMiddleware` (bloque l'accès avant configuration)
- ✅ Dashboard Admin École (tableau de bord personnalisé)
- ✅ Tests automatisés (isolation, permissions, flux)

**Stabilisation :**

- Audit du code, des migrations, des routes, des formulaires, des templates et
  des tests réalisé
- Contrôles Django et migrations validés
- Suite de tests Phase 1 validée : 83 tests réussis
- Permissions de base et isolation des écoles vérifiées côté backend
- Messages de création nettoyés : aucun mot de passe temporaire dans un
  message de redirection

**Améliorations UX/UI :**

- Connexion responsive avec erreurs explicites et message non révélateur
- Assistant en 3 étapes avec progression visible, validation serveur et reprise
  possible
- Interfaces Bootstrap cohérentes sur ordinateur et mobile

**Documentation :**

- Rapport de stabilisation : `docs/phase-1-stabilisation.md`
- Architecture, multi-tenant, permissions et lancement documentés dans `docs/`

**Ce qui reste hors Phase 1 :**

- Envoi automatisé des identifiants par email (nécessite SMTP)
- Interface de gestion des abonnements

### Phase 2 — Inscription & Dossier Élève
**Statut : 🏗️ Architecture prête**

### Phase 3 — Personnel Enseignant
**Statut : 🏗️ Architecture prête**

### Phase 4 — Emploi du Temps
**Statut : 🏗️ Architecture prête**

### Phase 5 — Paiement Scolaire
**Statut : 🏗️ Architecture prête**

### Phase 6 — Ressources Pédagogiques
**Statut : 🏗️ Architecture prête**

### Phase 7 — Portail Parents/Élèves (PWA)
**Statut : 🏗️ Architecture prête**

### Phase 8 — Gestion des Années Scolaires
**Statut : 🏗️ Architecture prête**

---

## Démarrage rapide (développement sur Replit)

```bash
# 1. Les variables d'environnement sont gérées par Replit
#    DATABASE_URL est fourni automatiquement

# 2. Installer les dépendances
pip install -r requirements/development.txt

# 3. Appliquer les migrations
python manage.py migrate_schemas --shared
python manage.py migrate_schemas

# 4. Créer un Super Admin
python manage.py shell -c "
from apps.accounts.models import User
from apps.core.constants import Roles
User.objects.create_superuser(
    email='super@klass.app',
    password='SuperAdmin123!',
    first_name='Super',
    last_name='Admin',
    role=Roles.SUPER_ADMIN,
)
"

# 5. Lancer le serveur
python manage.py runserver 0.0.0.0:5000
```

## Démarrage rapide (développement local)

### Prérequis

- Python 3.11+
- PostgreSQL 14+
- Redis 7+ (optionnel — `CELERY_TASK_ALWAYS_EAGER=True` pour le développement)

### Installation

```bash
# 1. Variables d'environnement
cp .env.example .env
# Éditez .env avec vos valeurs

# 2. Dépendances
pip install -r requirements/development.txt

# 3. Migrations
python manage.py migrate_schemas --shared
python manage.py migrate_schemas

# 4. Super Admin
python manage.py createsuperuser

# 5. Serveur
python manage.py runserver
```

---

## Flux principal (Phase 1)

```
Super Admin
    ↓  /super-admin/
Dashboard Super Admin (liste des écoles)
    ↓  /super-admin/schools/create/
Création de l'école + tenant PostgreSQL + Admin École
    ↓  /super-admin/schools/creation-success/
Page de confirmation (affichage unique des identifiants)
  → Email, mot de passe temporaire, lien de connexion
  → Boutons de copie (individuel + global)
  → Effacés de la session dès la première lecture
    ↓
Super Admin transmet les identifiants à l'Admin École
    ↓  /auth/login/
Première connexion → changement obligatoire du mot de passe
    ↓  /super-admin/setup/school-info/
Assistant de configuration :
  1. Informations de l'école
  2. Année scolaire initiale
  3. Confirmation
    ↓  /academics/
Dashboard de l'école (opérationnelle)
```

---

## Rôles

| Rôle | Description | Redirection après login |
|------|-------------|------------------------|
| `super_admin` | Gère les écoles clientes (accès global) | `/super-admin/` (dashboard super-admin) |
| `school_admin` | Directeur d'établissement (accès complet à son école) | Setup wizard → `academics:dashboard` |
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
- [**Phase 1 — Fondation de l'école**](docs/modules/phase-1-fondation-ecole.md) ← Nouveau
- [**Stabilisation Phase 1**](docs/phase-1-stabilisation.md)
