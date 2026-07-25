# Phase 3.1 — Inscriptions et Affectation des Élèves aux Classes

**Statut : ✅ TERMINÉE, STABILISÉE ET VALIDÉE**

---

## Objectif

La Phase 3.1 implémente le système d'inscription qui lie un élève à une classe pour une année scolaire donnée. L'élève lui-même n'est pas directement lié à une classe — c'est **l'inscription** qui détermine le placement d'un élève pour une année.

```
Élève
  ↓
Inscription (StudentEnrollment)
  ↓
Année scolaire
  ↓
Classe
```

---

## Modèle d'inscription

### `StudentEnrollment` (`apps/students/models.py`)

| Champ | Type | Description |
|-------|------|-------------|
| `student` | FK → Student | L'élève inscrit |
| `school_year` | FK → SchoolYear | L'année scolaire |
| `classroom` | FK → Classroom | La classe |
| `status` | CharField | Statut de l'inscription |
| `enrollment_date` | DateField | Date d'inscription (auto) |
| `enrolled_by` | FK → User | Qui a créé l'inscription |
| `notes` | TextField | Notes libres |

---

## Statuts d'inscription

| Code | Libellé | Actif ? |
|------|---------|---------|
| `pending` | En attente | ✅ |
| `active` | Active | ✅ |
| `completed` | Terminée | ❌ |
| `cancelled` | Annulée | ❌ |
| `transferred` | Transféré | ❌ (rétro-compat) |
| `graduated` | Diplômé | ❌ (rétro-compat) |
| `dropped` | Abandonné | ❌ (rétro-compat) |
| `repeating` | Redoublant | ❌ (rétro-compat) |

Les statuts **actifs** sont `pending` et `active`. Ils sont regroupés dans `EnrollmentStatus.ACTIVE_STATUSES`.

---

## Règles métier

### 1. Une seule inscription active par élève et par année

Un élève ne peut pas avoir deux inscriptions actives pour la même année scolaire. La règle est appliquée :
- Dans `StudentEnrollment.clean()` (validation modèle)
- Dans `EnrollmentForm.clean()` (validation formulaire)
- Dans `EnrollmentStatusChangeView` (changement de statut)

```python
# Exemple interdit :
Élève A → 2026-2027 → Classe A (active)
Élève A → 2026-2027 → Classe B (active)  # ❌ Validation error

# Exemple autorisé :
Élève A → 2024-2025 → Classe A (terminée)
Élève A → 2025-2026 → Classe B (active)  # ✅
```

### 2. Historique préservé

Les anciennes inscriptions ne sont jamais supprimées. Un élève accumule un historique scolaire visible dans sa fiche et dans la fiche de chaque inscription.

### 3. Changement de classe

Le changement de classe est tracé :
1. L'inscription courante est marquée `Terminée`
2. Une note est ajoutée : `[Changement de classe vers Nouvelle Classe]`
3. Une nouvelle inscription est créée dans la nouvelle classe

### 4. Capacité des classes

La classe `Classroom` possède un champ `capacity`. La vue `ClassroomEnrollmentsView` affiche le taux de remplissage. **Attention** : le dépassement de capacité est visible mais non bloquant (à affiner selon politique de l'école).

---

## Isolation multi-tenant

Toutes les requêtes utilisent `schema_context(school.schema_name)` :
- La sélection des années scolaires est filtrée par école
- La sélection des classes est filtrée par école + année
- Aucune donnée cross-école ne peut apparaître

---

## Routes

| URL | Nom | Vue |
|-----|-----|-----|
| `students/enrollments/` | `students:enrollment_list` | Liste des inscriptions |
| `students/enrollments/create/` | `students:enrollment_create` | Créer une inscription |
| `students/enrollments/<pk>/` | `students:enrollment_detail` | Détail |
| `students/enrollments/<pk>/edit/` | `students:enrollment_edit` | Modifier statut/notes |
| `students/enrollments/<pk>/change-class/` | `students:enrollment_change_class` | Changer de classe |
| `students/enrollments/<pk>/status/` | `students:enrollment_status` | Changement rapide de statut |
| `students/classrooms/<pk>/enrollments/` | `students:classroom_enrollments` | Élèves d'une classe |
| `students/api/classrooms-for-year/` | `students:api_classrooms_for_year` | API : classes par année (JSON) |
| `students/api/search/` | `students:api_search` | API : recherche élève (JSON) |

---

## Interfaces

### Liste des inscriptions (`enrollment_list`)
- Filtres : recherche élève, année scolaire, statut, classe
- Colonnes : matricule, nom, année, niveau, option, classe, date, statut

### Création d'une inscription (`enrollment_create`)
- Sélection élève (liste)
- Sélection année scolaire → charge les classes dynamiquement via JavaScript
- Sélection classe (filtrée par année)
- Statut initial + notes
- Validation backend anti-doublon

### Détail d'une inscription (`enrollment_detail`)
- Informations complètes de l'inscription
- Changement de statut rapide
- Lien vers changement de classe
- Historique complet du parcours de l'élève

### Changement de classe (`enrollment_change_class`)
- Sélection de la nouvelle classe (même année, classes actives uniquement)
- Motif du changement (optionnel)
- Traçabilité garantie

### Fiche élève (`students:detail`)
- Affiche l'inscription active courante en évidence
- Tableau de tout l'historique scolaire
- Bouton d'inscription si aucune inscription active

---

## Permissions

| Action | Rôle requis |
|--------|-------------|
| Consulter les inscriptions | Personnel de l'école |
| Créer une inscription | Admin École |
| Modifier une inscription | Admin École |
| Changer de classe | Admin École |
| Changer le statut | Admin École |

---

## Tests

Fichier : `tests/test_phase31_enrollments.py`

- `TestEnrollmentModel::test_enrollment_creation` — création basique
- `TestEnrollmentModel::test_no_duplicate_active_enrollment` — règle unicité
- `TestEnrollmentModel::test_cancelled_enrollment_allows_new_active` — re-inscription après annulation
- `TestEnrollmentModel::test_enrollment_history_multiple_years` — historique multi-années
- `TestEnrollmentModel::test_current_enrollment_property` — propriété current_enrollment
- `TestEnrollmentModel::test_pending_enrollment_is_active` — statut pending = actif
- `TestEnrollmentModel::test_enrollment_cancel_method` — méthode cancel()
- `TestEnrollmentModel::test_status_badge_class` — badge CSS
- `TestEnrollmentModel::test_two_students_same_classroom` — deux élèves même classe
- `TestEnrollmentStatusConstants` — constantes de statut

---

## Données de test

Le script `scripts/seed_data.py` crée les inscriptions suivantes :

| Élève | Année | Classe | Statut |
|-------|-------|--------|--------|
| Jean Kabila | 2024-2025 | 5ème Sci A | Terminée |
| Jean Kabila | 2025-2026 | 6ème Sci A | Active |
| Claire Mutombo | 2025-2026 | 5ème Sci A | Active |
| Pierre Tshombe | 2025-2026 | 6ème Sci B | En attente |

---

## Migration

`apps/students/migrations/0004_phase31_enrollment_history.py`
- Suppression de `unique_together` sur `(student, school_year)`
- Ajout des nouveaux choix de statut (`pending`, `completed`, `cancelled`)
