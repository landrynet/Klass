---
name: Phase 2.1 — Classes et Salles
description: Patterns utilisés pour implémenter les modèles Classroom et Room avec statuts et isolation tenant
---

# Phase 2.1 — Classes et Salles

## Règle : statuts Classroom

- `is_active` (default True) + `is_archived` (default False)
- Archivage force `is_active=False`
- Classe archivée = lecture seule (vérification en GET et POST des vues d'édition)
- Propriétés `status_display` et `status_badge_class` calculées sur le modèle

## Règle : statuts Room

- `is_available` (existant) = hors service temporaire
- `is_archived` (ajouté Phase 2.1, default False) = retrait définitif
- Salle archivée = lecture seule, ne peut plus être assignée à une classe

**Why:** Cohérence avec le pattern SchoolYear (is_active + is_archived), et permet aux vues de classroom d'exclure les salles archivées du queryset `main_room`.

## Convention : isolation tenant dans les vues

Les querysets d'options et de salles pour les formulaires de classe sont construits **dans le même `schema_context`** que la vue. Cela garantit qu'on ne peut pas assigner une salle d'une autre école.

## Migration appliquée

Migration `0004_classroom_status_room_archived` sur `apps.academics`.

## Tests

Fichier `tests/test_phase21_classes_salles.py` — 143 tests total (0 échec).
Les 2 tests préexistants dans `test_models.py` corrigés (assertions "ACTIVE"/"CLÔTURÉE" → "Active"/"Terminée").
