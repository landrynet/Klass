# Commande `reset_test_data`

> Commande de gestion Django pour réinitialiser les données de test dans l'environnement de développement.

---

## Usage

```bash
python manage.py reset_test_data [options]
```

### Options

| Option              | Description                                       |
|---------------------|---------------------------------------------------|
| `--schema SCHEMA`   | Schéma tenant cible (défaut : `ecole_demo`)       |
| `--yes` / `-y`      | Ignorer la demande de confirmation interactive    |
| `--skip-confirm`    | Alias de `--yes`                                  |

### Exemples

```bash
# Réinitialisation interactive (demande confirmation)
python manage.py reset_test_data

# Réinitialisation sans confirmation (CI / scripts)
python manage.py reset_test_data --yes

# Cibler un schéma spécifique
python manage.py reset_test_data --schema mon_ecole_test --yes
```

---

## Prérequis

- `DEBUG=True` dans les settings (la commande refuse de s'exécuter en production)
- Le schéma tenant spécifié doit exister

---

## Ce que fait la commande

1. **Vérifie** `DEBUG=True` — erreur sinon
2. **Demande confirmation** — sauf si `--yes` passé
3. **Purge** : inscriptions → élèves → parents → classes → options → niveaux → années → personnel → salles
4. **Recrée** :
   - 3 années scolaires (2022-2023 archivée, 2023-2024 terminée, 2024-2025 active)
   - 6 niveaux secondaires × 3 options = 18 filières
   - ~24 classes pour l'année active (2 classes pour S1 et S2)
   - 8 salles de cours
   - 12 enseignants + 5 administratifs
   - 55 élèves avec 30 parents
   - ~55 inscriptions actives + ~30 inscriptions complétées
5. **Affiche un résumé** des comptages créés

---

## Données générées

### Années scolaires

| Nom       | Statut   |
|-----------|----------|
| 2022-2023 | Archivée |
| 2023-2024 | Terminée |
| 2024-2025 | Active   |

### Niveaux & Options

6 niveaux (S1→S6) × 3 options (Sciences / Littéraire / Commercial)

### Élèves

55 élèves avec prénoms et noms générés aléatoirement, chacun associé à un parent principal. ~30% ont un second contact.

---

## Sécurité

La commande est protégée par le guard `DEBUG=True`. En production, elle lève `CommandError` avant toute modification.
