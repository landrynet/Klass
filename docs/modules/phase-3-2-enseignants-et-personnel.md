# Phase 3.2 — Enseignants et personnel scolaire

**Statut : ✅ TERMINÉE, STABILISÉE ET VALIDÉE**

## Objectif

Le module fournit un dossier professionnel tenant-isolé pour chaque membre du
personnel. Un dossier est indépendant d'un compte de connexion : le lien vers
`accounts.User` est optionnel.

## Modèles

- `Personnel` : identité, coordonnées, type, statut, expérience, diplôme,
  contrat et compte optionnel.
- `Teacher` : profil enseignant lié à `Personnel`, conservant les relations
  extensibles avec `Subject`, `TeacherSubject`, `TeacherAvailability` et le
  futur emploi du temps.
- `PersonnelNumberConfiguration` : compteur par tenant. Les matricules sont
  générés côté backend (`ENS-AAAA-0001` pour un enseignant et `PER-AAAA-0001`
  pour les autres personnels), uniques et non saisis dans les formulaires.

Types : enseignant, administratif, direction, technique, autre.
Statuts : actif, inactif, en congé, suspendu, archivé. L'archivage conserve
l'historique et n'efface pas le dossier.

## Permissions et isolation

- Lecture des listes et fiches : personnel scolaire autorisé.
- Création, modification et changement de statut : Admin École uniquement.
- Toutes les requêtes sont réalisées dans `schema_context(request.user.school.schema_name)`.
- Les détails utilisent `get_object_or_404` dans le schéma courant : un
  identifiant d'une autre école ne donne aucune donnée.

## Routes principales

| Route | Nom | Fonction |
|---|---|---|
| `/teachers/` | `teachers:list` | Liste des enseignants |
| `/teachers/create/` | `teachers:create` | Créer un enseignant |
| `/teachers/<pk>/` | `teachers:teacher_detail` | Détail enseignant |
| `/teachers/personnel/` | `teachers:personnel_list` | Tout le personnel |
| `/teachers/personnel/create/` | `teachers:personnel_create` | Créer un membre |
| `/teachers/personnel/<pk>/` | `teachers:personnel_detail` | Détail personnel |
| `/teachers/personnel/<pk>/edit/` | `teachers:personnel_edit` | Modifier |
| `/teachers/personnel/<pk>/status/` | `teachers:personnel_status` | Changer le statut |

## Données de test

`python scripts/seed_data.py` est idempotent et crée deux enseignants avec
spécialités/statuts différents, ainsi qu'un personnel administratif et
technique. Il conserve les données des phases précédentes.

## Vérifications

Les tests couvrent la génération, l'unicité et la stabilité des matricules,
les types/statuts, la création d'un profil enseignant sans compte, les
recherches/filtres et les permissions des routes.

Le module des matières, affectations complètes, emploi du temps, évaluations,
notes et présences restent réservés aux phases futures.