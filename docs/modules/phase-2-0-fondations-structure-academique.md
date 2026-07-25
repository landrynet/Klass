# Phase 2.0 — Fondations de la Structure Académique

**Statut : ✅ TERMINÉE, STABILISÉE ET VALIDÉE**

---

## Objectif

Construire les fondations de la structure académique de KLASS au-dessus de l'infrastructure multi-tenant de la Phase 1.

La hiérarchie implémentée :

```
École (tenant PostgreSQL)
    ↓
Années scolaires
    ↓
Niveaux d'études
    ↓
Options / Filières
    ↓
Phase 2.1 : Classes et Salles (à venir)
```

---

## Ajustements Phase 1 (Partie A)

### Informations d'accès après création d'une école

Le flux de création d'école existant a été vérifié et est fonctionnel :

- Le Super Admin crée une école via `/super-admin/schools/create/`
- Les identifiants sont stockés en session (`school_creation_credentials`)
- La page de confirmation (`/super-admin/schools/creation-success/`) les affiche **une seule fois**
- Les identifiants sont effacés de la session dès la première lecture (`session.pop`)
- Le mot de passe temporaire n'est jamais stocké en clair en base (Django hash)
- Le template `creation_success.html` offre des boutons "Copier" individuels et "Copier tout"

### Sécurité du mot de passe temporaire

- `must_change_password=True` est mis sur l'Admin École à la création
- À la première connexion, l'utilisateur est redirigé vers le changement obligatoire
- Après le changement, `must_change_password` est mis à `False`
- Le mot de passe ne peut plus être consulté ensuite

---

## Fonctionnalités développées

### 1. Gestion complète des années scolaires

**Modèle** : `apps/school_years/models.py` → `SchoolYear`

**Champs ajoutés en Phase 2.0** :
- `is_archived` (BooleanField, défaut=False) — 4ème état du cycle de vie

**Cycle de vie (4 états)** :

| État | is_active | is_closed | is_archived | Description |
|------|-----------|-----------|-------------|-------------|
| Planifiée | False | False | False | Créée, en attente d'activation |
| Active | True | False | False | Année courante |
| Terminée | False | True | False | Clôturée, données en lecture |
| Archivée | False | True | True | Définitivement fermée |

**Propriétés** :
- `status` → code de statut ('planned', 'active', 'ended', 'archived')
- `status_display` → libellé en français
- `status_badge_class` → classe CSS Bootstrap pour le badge
- `is_editable` → False si clôturée ou archivée
- `can_activate`, `can_end`, `can_archive` → transitions autorisées

**Méthodes de transition** :
- `activate(save=True)` — désactive les autres, active celle-ci
- `end(closed_by=None, save=True)` — clôture
- `archive(save=True)` — archive définitivement

**Services** : `apps/school_years/services.py`
- `activate_school_year(school, year_pk, activated_by)`
- `end_school_year(school, year_pk, closed_by)`
- `archive_school_year(school, year_pk)`
- `create_school_year(school, name, start_date, end_date, activate, created_by)`
- `update_school_year(school, year_pk, name, start_date, end_date)`

**Interface** :
- Liste : `/school-years/` — avec badges de statut et boutons d'action contextuels
- Création : `/school-years/create/`
- Modification : `/school-years/<pk>/edit/`
- Actions POST : `/school-years/<pk>/activate/`, `/end/`, `/archive/`

**Compatibilité Phase 1** : La logique de création de l'année initiale dans l'assistant (`SetupSchoolYearView`) continue de fonctionner sans modification. Elle utilise directement `SchoolYear.objects.create(is_active=True)`, ce qui est compatible.

---

### 2. Niveaux scolaires

**Modèle** : `apps/academics/models.py` → `Level`

**Champs ajoutés en Phase 2.0** :
- `is_active` (BooleanField, défaut=True) — active/désactive le niveau

**Relations** :
```
SchoolYear (1) → Level (N)
Level (1) → Option (N)
```

**Contrainte d'unicité** : `(school_year, name)` — deux niveaux du même nom dans la même année sont interdits.

**Isolation tenant** : `Level` hérite de `TenantAwareModel`, stocké dans le schéma PostgreSQL de l'école. Impossible d'accéder aux niveaux d'une autre école.

**Interface** :
- Liste filtrée par année : `/academics/levels/?year_id=<pk>`
- Création : `/academics/levels/create/`
- Modification : `/academics/levels/<pk>/edit/`
- Activation/désactivation : POST `/academics/levels/<pk>/toggle/`

**Permissions** :
- Lecture : tous les rôles du personnel (`SCHOOL_STAFF_ROLES`)
- Écriture : `school_admin` uniquement

---

### 3. Options / Filières

**Modèle** : `apps/academics/models.py` → `Option`

**Champs ajoutés en Phase 2.0** :
- `is_active` (BooleanField, défaut=True) — active/désactive l'option

**Relations** :
```
Level (1) → Option (N)
Option (1) → Classroom (N) [Phase 2.1]
```

**Contrainte d'unicité** : `(level, name)` — deux options du même nom dans le même niveau sont interdites.

**Isolation tenant** : `Option` hérite de `TenantAwareModel`. L'isolation est garantie au niveau du schéma PostgreSQL et validée côté backend (pas seulement en UI).

**Interface** :
- Liste filtrée par année puis par niveau : `/academics/options/?year_id=<pk>&level_id=<pk>`
- Création : `/academics/options/create/?level_id=<pk>`
- Modification : `/academics/options/<pk>/edit/`
- Activation/désactivation : POST `/academics/options/<pk>/toggle/`

**Permissions** : identiques aux niveaux (lecture = staff, écriture = school_admin).

---

## Modèles et relations

```
SchoolYear (tenant)
├── name           : "2025-2026"
├── start_date     : date
├── end_date       : date
├── is_active      : bool
├── is_closed      : bool
├── is_archived    : bool  ← nouveau Phase 2.0
├── closed_at      : datetime?
└── closed_by      : FK User?

Level (tenant)
├── school_year    : FK SchoolYear
├── name           : "1ère secondaire"
├── code           : "1SEC"
├── order          : int (tri)
└── is_active      : bool  ← nouveau Phase 2.0

Option (tenant)
├── level          : FK Level
├── name           : "Scientifique"
├── code           : "SCI"
├── description    : text
└── is_active      : bool  ← nouveau Phase 2.0
```

---

## Sécurité et isolation

### Isolation multi-tenant

Toutes les vues utilisent `schema_context(school.schema_name)` pour les requêtes tenant-spécifiques. Cela garantit que :
- Un utilisateur de l'École A ne peut pas accéder aux données de l'École B
- Les URL manipulées (ex : `?year_id=99`) n'exposent que les données du tenant courant
- Les PKs d'une école ne sont pas accessibles depuis une autre école

### Vérifications backend

Chaque vue vérifie :
1. Authentification (`login_required`)
2. Rôle (`school_admin` ou `SCHOOL_STAFF_ROLES`)
3. Existence de l'école associée (`request.user.school`)
4. Requêtes dans le bon schéma (`schema_context`)
5. Unicité des noms (côté serveur, pas seulement côté formulaire)

### Ce qui est vérifié contre les attaques URL

- Accès à `/academics/levels/99/edit/` avec le PK d'un autre tenant → 404 (le PK n'existe pas dans ce schéma)
- Modification du `year_id` en URL → seulement les années du tenant courant sont retournées
- Soumission d'un `level_id` étranger → 404 dans le schema_context courant

---

## Routes

### Années scolaires (`/school-years/`)

| URL | Nom | Méthode | Description |
|-----|-----|---------|-------------|
| `/school-years/` | `school_years:list` | GET | Liste |
| `/school-years/create/` | `school_years:create` | GET, POST | Création |
| `/school-years/<pk>/edit/` | `school_years:edit` | GET, POST | Modification |
| `/school-years/<pk>/activate/` | `school_years:activate` | POST | Activation |
| `/school-years/<pk>/end/` | `school_years:end` | POST | Clôture |
| `/school-years/<pk>/archive/` | `school_years:archive` | POST | Archivage |

### Niveaux (`/academics/levels/`)

| URL | Nom | Méthode | Description |
|-----|-----|---------|-------------|
| `/academics/levels/` | `academics:levels` | GET | Liste |
| `/academics/levels/create/` | `academics:level_create` | GET, POST | Création |
| `/academics/levels/<pk>/edit/` | `academics:level_edit` | GET, POST | Modification |
| `/academics/levels/<pk>/toggle/` | `academics:level_toggle` | POST | Activer/désactiver |

### Options (`/academics/options/`)

| URL | Nom | Méthode | Description |
|-----|-----|---------|-------------|
| `/academics/options/` | `academics:options` | GET | Liste |
| `/academics/options/create/` | `academics:option_create` | GET, POST | Création |
| `/academics/options/<pk>/edit/` | `academics:option_edit` | GET, POST | Modification |
| `/academics/options/<pk>/toggle/` | `academics:option_toggle` | POST | Activer/désactiver |

---

## Recherche et filtres

### Années scolaires
- Liste complète (toutes les années, triées par `start_date` décroissant)
- Pas de recherche textuelle (nombre limité d'années)

### Niveaux
- Filtre par année scolaire via `?year_id=<pk>` (défaut : année active)
- Tri par `order` puis `name`

### Options / Filières
- Filtre par année scolaire puis par niveau via `?year_id=<pk>&level_id=<pk>`
- Sélecteur automatique du premier niveau si aucun n'est spécifié

---

## Données de test

Le script `scripts/seed_data.py` a été mis à jour pour inclure les données Phase 2.0.

Pour exécuter (idempotent) :
```bash
python scripts/seed_data.py
```

Données ajoutées pour l'école de démo :
- Années : `2025-2026 [SEED]`, `2026-2027 [SEED]`
- Niveaux : 1ère à 6ème secondaire
- Options : Scientifique, Littéraire, Commerciale (sur chaque niveau)

---

## Tests

Fichiers de tests Phase 2.0 :
- `tests/test_school_years.py` — modèle, transitions d'état, formulaires
- `tests/test_academics_phase2.py` — Level, Option, formulaires, isolation

Exécution :
```bash
DJANGO_SETTINGS_MODULE=config.settings.development python -m pytest tests/ -v
```

---

## Préparation pour la Phase 2.1

Les structures suivantes sont prêtes à être étendues en Phase 2.1 :

- **Classes** (`Classroom`) : modèle existant, lié à `Option` et `SchoolYear`
- **Salles** (`Room`) : modèle existant, indépendant des années
- Les routes `/academics/classrooms/` et `/academics/rooms/` sont définies (redirigent temporairement vers le dashboard)
- La relation `Option → Classroom` est en place pour accueillir les classes

---

## Problèmes connus

- En environnement de développement Replit (accès via localhost), le middleware multi-tenant n'associe pas automatiquement un schéma. Les vues utilisent `schema_context` explicitement comme solution.
- Les templates de classrooms, rooms et subjects sont des placeholders (Phase 2.1).
