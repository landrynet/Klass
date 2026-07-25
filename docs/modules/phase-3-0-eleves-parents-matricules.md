# Phase 3.0 — Élèves, parents et matricules

**Statut : ✅ TERMINÉE, STABILISÉE ET VALIDÉE**

## Fonctionnalités

- Dossier élève permanent avec nom, prénom, date de naissance, genre et statut.
- Parent ou tuteur avec coordonnées, recherche et détection des doublons évidents.
- Un parent peut être associé à plusieurs élèves; chaque élève possède un parent principal.
- Matricule généré côté serveur avec compteur verrouillé par transaction.
- Format configurable par école : préfixe, année, séparateur, padding et prochain numéro.
- Les changements de format n'altèrent jamais les matricules déjà attribués.
- Interfaces personnalisées pour listes, recherche, consultation et modification.

## Sécurité

Toutes les opérations métier utilisent `schema_context(request.user.school.schema_name)`.
Les querysets de parents sont injectés dans les formulaires depuis le tenant courant,
et les rôles d'écriture restent limités à `school_admin`.

## Routes

- `/students/` : liste et recherche des élèves
- `/students/create/` : création avec parent principal obligatoire
- `/students/parents/` : liste et recherche des parents
- `/students/parents/create/` : création avec alerte de doublon
- `/students/matricules/configuration/` : configuration du format

Les inscriptions et l'affectation à une classe restent réservées à la phase 3.1.

## Vérification

Les migrations sont `apps/students/migrations/0001_initial.py` et
`0002_phase3.py`. Le curseur PostgreSQL est configuré en binding client pour
éviter qu'un queryset de formulaire soit évalué après la fermeture du contexte tenant.