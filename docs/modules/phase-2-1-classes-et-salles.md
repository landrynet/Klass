# Phase 2.1 — Gestion des Classes et des Salles

**Statut : ✅ TERMINÉE, STABILISÉE ET VALIDÉE**

---

## Objectif

Construire la suite logique de l'architecture académique :

```
École
  ↓
Année scolaire
  ↓
Niveau
  ↓
Option / Filière
  ↓
Classe        ← Phase 2.1
  ↓
Salle         ← Phase 2.1
```

---

## Fonctionnalités

### Salles

- Création, modification, consultation
- Activation / désactivation (disponible / indisponible)
- Archivage (réversible)
- Recherche par nom / code
- Filtres par type et statut
- Isolation multi-tenant : chaque salle appartient au schéma PostgreSQL de son école

### Classes

- Création, modification, consultation
- Activation / désactivation
- Archivage (réversible ; archive automatiquement désactive)
- Filtres par année scolaire, niveau, option, statut
- Recherche par identifiant
- Association à une salle principale (optionnelle)
- Isolation multi-tenant : toutes les FK sont vérifiées dans le même schéma

---

## Modèles

### `Room` (mise à jour Phase 2.1)

| Champ | Type | Description |
|-------|------|-------------|
| `name` | CharField(100) | Nom / numéro de salle |
| `code` | CharField(20) | Code court (ex: S01) — **nouveau** |
| `room_type` | CharField | Type : classroom, laboratory, computer_lab, library, gymnasium, **polyvalent**, other |
| `capacity` | PositiveSmallIntegerField | Capacité maximale |
| `equipment` | JSONField | Liste d'équipements |
| `is_available` | BooleanField | Disponible / Indisponible (hors service temporaire) |
| `is_archived` | BooleanField | Archivée — **nouveau** |
| `floor` | CharField(20) | Étage / Bâtiment |
| `notes` | TextField | Notes libres |

**Propriétés calculées** : `status_display`, `status_badge_class`

### `Classroom` (mise à jour Phase 2.1)

| Champ | Type | Description |
|-------|------|-------------|
| `school_year` | FK → SchoolYear | Année scolaire |
| `option` | FK → Option | Option / filière (contient le niveau) |
| `name` | CharField(50) | Identifiant de section (ex: A, B) |
| `capacity` | PositiveSmallIntegerField | Capacité maximale |
| `main_room` | FK → Room (nullable) | Salle principale assignée |
| `is_active` | BooleanField | Active / Inactive — **nouveau** |
| `is_archived` | BooleanField | Archivée — **nouveau** |

**Propriétés calculées** : `full_name`, `status_display`, `status_badge_class`

---

## Relations

```
SchoolYear ──┐
             │
Level ←──────┤
             │
Option ←─────┘
   │
   └──► Classroom ──► Room (optionnel)
```

- Une classe ne peut jamais être associée à une salle d'une autre école : les querysets de salles sont filtrés dans le même `schema_context`.
- L'unicité `(school_year, option, name)` empêche deux classes identiques tout en autorisant A, B, C pour la même option.

---

## Règles métier

### Classes

- Unicité : `(school_year, option, name)` — ex: 6ème Scientifique A est unique
- Plusieurs sections du même niveau/option sont autorisées : A, B, C sont valides
- Une classe archivée est automatiquement désactivée
- Une classe archivée ne peut plus être modifiée (protection en vue et en POST)
- La salle assignée doit appartenir au même schéma tenant

### Salles

- Unicité du nom dans l'école (hors salles archivées)
- Une salle archivée ne peut plus être modifiée
- `is_available` = hors service temporaire (pas d'inscription possible)
- `is_archived` = retrait définitif (réversible)
- La capacité doit être ≥ 1

---

## Statuts

### Classes

| Statut | is_active | is_archived | Badge |
|--------|-----------|-------------|-------|
| Active | True | False | Vert |
| Inactive | False | False | Gris |
| Archivée | False | True | Rouge |

### Salles

| Statut | is_available | is_archived | Badge |
|--------|-------------|-------------|-------|
| Disponible | True | False | Vert |
| Indisponible | False | False | Orange |
| Archivée | — | True | Rouge |

---

## Permissions

| Action | Rôle requis |
|--------|-------------|
| Voir la liste des classes | Tout le personnel (`SCHOOL_STAFF_ROLES`) |
| Voir la liste des salles | Tout le personnel |
| Créer / modifier / archiver | `school_admin` uniquement |
| Activer / désactiver | `school_admin` uniquement |

---

## Sécurité et isolation multi-tenant

Toutes les vues utilisent `schema_context(school.schema_name)` pour isoler les données.

- Les querysets d'options, salles et classes sont toujours filtrés dans le schéma courant.
- Une salle d'une autre école ne peut pas être assignée à une classe (le queryset de salles est construit dans le même `schema_context`).
- La vérification d'unicité s'effectue côté backend (pas seulement en UI).
- Les vues d'édition vérifient l'archivage avant de permettre toute modification.

---

## Routes

### Salles

| Méthode | URL | Nom | Description |
|---------|-----|-----|-------------|
| GET | `/academics/rooms/` | `academics:rooms` | Liste avec filtres |
| GET/POST | `/academics/rooms/create/` | `academics:room_create` | Création |
| GET/POST | `/academics/rooms/<pk>/edit/` | `academics:room_edit` | Modification |
| POST | `/academics/rooms/<pk>/toggle/` | `academics:room_toggle` | Disponible/Indisponible |
| POST | `/academics/rooms/<pk>/archive/` | `academics:room_archive` | Archiver/Désarchiver |

### Classes

| Méthode | URL | Nom | Description |
|---------|-----|-----|-------------|
| GET | `/academics/classrooms/` | `academics:classrooms` | Liste avec filtres |
| GET/POST | `/academics/classrooms/create/` | `academics:classroom_create` | Création |
| GET/POST | `/academics/classrooms/<pk>/edit/` | `academics:classroom_edit` | Modification |
| POST | `/academics/classrooms/<pk>/toggle/` | `academics:classroom_toggle` | Activer/Désactiver |
| POST | `/academics/classrooms/<pk>/archive/` | `academics:classroom_archive` | Archiver/Désarchiver |

---

## Interfaces

### Liste des salles (`/academics/rooms/`)

- Filtres : type, statut (disponible / indisponible / archivée), recherche texte
- Tableau : nom, code, type, capacité, étage, statut
- Actions : modifier, toggle disponibilité, archiver/désarchiver

### Liste des classes (`/academics/classrooms/`)

- Filtres : année scolaire, niveau, option, statut, recherche
- Tableau : nom complet, niveau · option, capacité, salle, statut
- Actions : modifier, activer/désactiver, archiver/désarchiver

---

## Données de test

Créées par `python scripts/seed_data.py` (idempotent) :

**Salles** :
- Salle 01 [SEED] — Salle de classe, 50 places, RDC
- Salle 02 [SEED] — Salle de classe, 50 places, RDC
- Laboratoire [SEED] — Laboratoire, 30 places, 1er étage
- Salle Informatique [SEED] — Salle informatique, 25 places, 1er étage
- Salle Polyvalente [SEED] — Salle polyvalente, 80 places, RDC

**Classes** :
- 6ème secondaire Scientifique A (40 élèves → Salle 01)
- 6ème secondaire Scientifique B (40 élèves → Salle 02)
- 5ème secondaire Commerciale A (38 élèves → Salle 01)
- 4ème secondaire Littéraire A (35 élèves → Salle 02)

---

## Tests

Fichier : `tests/test_phase21_classes_salles.py`

- `TestRoomModel` — champs, statuts, propriétés, héritage
- `TestClassroomModel` — champs, statuts, propriétés, FK, héritage
- `TestClassroomForm` — champs, validation, nettoyage
- `TestRoomForm` — champs, code uppercase, nettoyage
- `TestPhase21TenantIsolation` — configuration TENANT_APPS
- `TestPhase20Regression` — régression Phase 2.0
- `TestPhase21URLs` — résolution de toutes les URLs Phase 2.1

---

## Migration

`apps/academics/migrations/0004_classroom_status_room_archived.py`

- Ajoute `Classroom.is_active` (default=True)
- Ajoute `Classroom.is_archived` (default=False)
- Ajoute `Room.code` (blank=True)
- Ajoute `Room.is_archived` (default=False)
- Ajoute le type `polyvalent` à `Room.room_type`

---

## Préparation des futurs modules

La structure est prête pour :

| Module | Ce qui est prêt |
|--------|-----------------|
| **Élèves** | `Classroom` avec capacité, `is_active` — l'enrollment peut référencer une classe |
| **Inscriptions** | `Classroom.capacity` permet de valider le plafond |
| **Emploi du temps** | `Room` avec `is_available`, `capacity`, `equipment` |
| **Enseignants** | `Classroom` identifie le groupe d'élèves |
| **Matières** | `Subject` ↔ `Level` (via SubjectLevel) déjà en place |
| **Évaluations** | `Classroom` identifie le contexte d'évaluation |
