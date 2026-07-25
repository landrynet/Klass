# Phase 1 — Fondation de l'école

**Statut : ⏳ EN COURS**

---

## 1. Objectif du module

La Phase 1 met en place la **fondation complète** permettant au Super Admin de créer une école et à l'Admin École de configurer son établissement avant d'utiliser les autres fonctionnalités du système.

---

## 2. Périmètre fonctionnel

Ce module couvre :
- La création d'une école par le Super Admin (interface personnalisée)
- La création du tenant PostgreSQL isolé (django-tenants)
- La génération et gestion du domaine de l'école
- La création automatique de l'Admin École
- La génération des identifiants temporaires sécurisés
- Le flux de première connexion avec changement de mot de passe obligatoire
- L'assistant de configuration initiale en 3 étapes
- Le dashboard de l'Admin École après configuration
- La sécurité et l'isolation multi-tenant

---

## 3. Fonctionnalités prévues

- [x] Interface Super Admin personnalisée (sans Django Admin)
- [x] Formulaire de création d'école (validation complète)
- [x] Création du tenant PostgreSQL via django-tenants
- [x] Création du domaine principal (slug.klass.app)
- [x] Création automatique de l'Admin École
- [x] Lien FK User → School pour l'identification de l'école
- [x] Génération d'identifiants temporaires sécurisés
- [x] Changement obligatoire du mot de passe à la première connexion
- [x] Assistant de configuration en 3 étapes :
  - [x] Étape 1 : Informations de l'école (nom, logo, adresse, contact)
  - [x] Étape 2 : Année scolaire initiale
  - [x] Étape 3 : Confirmation et activation
- [x] Middleware SetupRequiredMiddleware (bloque l'accès avant configuration)
- [x] Dashboard Super Admin (liste des écoles, statistiques)
- [x] Dashboard Admin École (après configuration)
- [x] Tests automatisés

---

## 4. Fonctionnalités développées

Toutes les fonctionnalités listées ci-dessus ont été implémentées dans cette phase.

---

## 5. Rôles et permissions

| Rôle | Dashboard Super Admin | Créer école | Assistant setup | Dashboard école |
|------|-----------------------|-------------|-----------------|-----------------|
| `super_admin` | ✅ | ✅ | ❌ (403) | ❌ |
| `school_admin` | ❌ (403) | ❌ | ✅ | ✅ (après setup) |
| Autres rôles | ❌ (403) | ❌ | ❌ (403) | ✅ (selon rôle) |

---

## 6. Modèles et données

### School (apps/tenants/models.py) — Schéma public
Champs principaux :
- `name`, `slug`, `schema_name` — identité du tenant
- `email`, `phone`, `address`, `city`, `country`, `logo` — coordonnées
- `is_active`, `setup_completed` — état
- `subscription_status` — abonnement

### Domain (apps/tenants/models.py) — Schéma public
- `tenant` (FK → School)
- `domain` — ex: ecole-a.klass.app
- `is_primary`

### User (apps/accounts/models.py) — Schéma public (SHARED_APPS)
Champ ajouté en Phase 1 :
- `school` (FK nullable → School) — lie l'utilisateur à son école

### SchoolYear (apps/school_years/models.py) — Schéma tenant
- `name`, `start_date`, `end_date`
- `is_active` — une seule année active à la fois

---

## 7. Architecture technique

### Applications concernées
- `apps/tenants` — modèles School/Domain, service de création, vues Super Admin + assistant
- `apps/accounts` — modèle User (ajout FK school), vues login/mot de passe
- `apps/core` — middleware TenantContextMiddleware + SetupRequiredMiddleware
- `apps/school_years` — modèle SchoolYear (créé dans le tenant lors du setup)
- `apps/academics` — vue DashboardView (tableau de bord de l'école)

### Services
- `apps/tenants/services.py` → `create_school_with_tenant()` : création atomique école + tenant + admin

### Middleware
- `TenantContextMiddleware` : injecte `request.current_school` depuis `request.tenant`
- `SetupRequiredMiddleware` : redirige l'Admin École vers l'assistant si `setup_completed=False`

### Formulaires
- `CreateSchoolForm` : création d'école par le Super Admin
- `SchoolInfoSetupForm` : étape 1 de l'assistant (ModelForm sur School)
- `SchoolYearSetupForm` : étape 2 de l'assistant (création SchoolYear)

---

## 8. Flux métier

```
Super Admin
    ↓
/super-admin/ → Dashboard (liste des écoles)
    ↓
/super-admin/schools/create/ → Formulaire de création
    ↓
create_school_with_tenant() :
    ├── Création School + schéma PostgreSQL
    ├── Création Domain (slug.klass.app)
    └── Création User (school_admin, must_change_password=True, school=FK)
    ↓
Identifiants temporaires affichés au Super Admin
    ↓

Admin École (première connexion)
    ↓
/auth/login/ → Connexion avec email + mot de passe temporaire
    ↓
Vérification must_change_password → /auth/change-password/
    ↓
Changement du mot de passe (must_change_password = False)
    ↓
Vérification setup_completed → /super-admin/setup/school-info/
    ↓
Étape 1 : Informations de l'école (nom, logo, adresse...)
    ↓
Étape 2 : Année scolaire initiale (créée dans le schéma tenant)
    ↓
Étape 3 : Confirmation → setup_completed = True
    ↓
/academics/ → Dashboard de l'école (opérationnelle)
```

---

## 9. Routes et interfaces

### Super Admin
| URL | Nom | Vue | Accès |
|-----|-----|-----|-------|
| `/super-admin/` | `tenants:super_admin_dashboard` | `SuperAdminDashboardView` | super_admin |
| `/super-admin/schools/create/` | `tenants:school_create` | `SchoolCreateView` | super_admin |
| `/super-admin/schools/<pk>/` | `tenants:school_detail` | `SchoolDetailView` | super_admin |

### Assistant de configuration
| URL | Nom | Vue | Accès |
|-----|-----|-----|-------|
| `/super-admin/setup/school-info/` | `tenants:setup_school_info` | `SetupSchoolInfoView` | school_admin |
| `/super-admin/setup/school-year/` | `tenants:setup_school_year` | `SetupSchoolYearView` | school_admin |
| `/super-admin/setup/confirm/` | `tenants:setup_confirm` | `SetupConfirmView` | school_admin |

### Templates créés
```
templates/
├── tenants/
│   ├── super_admin_dashboard.html
│   ├── schools/
│   │   ├── create.html
│   │   └── detail.html
│   └── setup/
│       ├── step_school_info.html
│       ├── step_school_year.html
│       └── confirm.html
├── academics/
│   └── dashboard.html  (mis à jour)
└── components/
    └── sidebar.html  (mis à jour)
```

---

## 10. Sécurité et isolation

### Isolation des données
- Chaque école a son propre schéma PostgreSQL (`school_<slug>`)
- Les données tenant (SchoolYear, etc.) sont créées via `schema_context(school.schema_name)`
- Le `SetupRequiredMiddleware` empêche l'accès aux modules avant la fin de la configuration
- Les vues vérifient le rôle côté serveur (PermissionDenied si accès non autorisé)

### Contrôles d'accès
- Super Admin : seul rôle autorisé à accéder au dashboard `/super-admin/`
- Admin École : seul rôle autorisé à accéder à l'assistant de configuration
- Middleware : vérifie `request.user.role`, `must_change_password`, `school.setup_completed`

### Sécurité des mots de passe
- Mot de passe temporaire généré aléatoirement (12 caractères, mixte majuscules/minuscules/chiffres/symboles)
- `must_change_password=True` à la création → changement obligatoire
- Validation Django des mots de passe (longueur min 8, complexité)
- Stockage via Django hash (jamais en clair)

---

## 11. Tests

Voir `apps/tenants/tests/test_phase1.py`.

### Couverture
- [x] Service `create_school_with_tenant` (création, doublons, slugs, domaines)
- [x] Admin École créé et lié à l'école
- [x] Isolation multi-tenant (École A ≠ École B)
- [x] Modèle School (`is_operational`, `is_trial`)
- [x] Modèle User (rôle, FK school, `must_change_password`)
- [x] Vues Super Admin (accès, permissions)
- [x] Flux de première connexion (redirection, middleware)

---

## 12. État du module

**⏳ EN COURS**

Le code est implémenté. Les tests restent à exécuter une fois la base de données configurée et les migrations appliquées.

---

## 13. Fonctionnalités restantes

- Pagination de la liste des écoles dans le dashboard Super Admin
- Désactivation / suspension d'une école
- Réinitialisation du mot de passe de l'Admin École
- Envoi des identifiants par email (quand SMTP configuré)
- Interface de gestion du profil de l'Admin École
- Test d'isolation PostgreSQL de bas niveau (schéma réel)

---

## 14. Problèmes connus

- En développement (localhost), `request.tenant` retourne le tenant public (pas le schéma école). La Phase 1 utilise `request.user.school` (FK) pour identifier l'école de l'admin, ce qui fonctionne en développement et production.
- La création des années scolaires utilise `schema_context()` qui nécessite que le schéma de l'école existe. En testing avec SQLite ou sans migration tenant, ces opérations peuvent échouer. Utiliser pytest-django avec `--reuse-db` est recommandé.
