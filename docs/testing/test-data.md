# Données de test KLASS

> Documentation du jeu de données de démonstration généré par `reset_test_data`.

---

## Accès au schéma de démo

L'école de démonstration tourne dans le schéma `ecole_demo`. Pour y accéder :

1. Naviguez vers `http://ecole-demo.localhost:5000/` (ou selon votre config `TENANT_DOMAIN`)
2. Connectez-vous avec le compte admin créé lors du setup

---

## Volume de données

| Entité        | Quantité        | Notes                            |
|---------------|-----------------|----------------------------------|
| Années scol.  | 3               | archived / ended / active        |
| Niveaux       | 6 × 2 années    | S1 → S6                          |
| Options       | 3 / niveau      | Sciences, Littéraire, Commercial |
| Classes       | ~24             | 2 classes pour S1/S2 actives     |
| Salles        | 8               | Bâtiments A, B, C, D             |
| Élèves        | 55              | Statut active                    |
| Parents       | 30              | ~1.8 élèves/parent               |
| Personnel     | 17              | 12 enseignants + 5 admin         |
| Inscriptions  | 55 actives + 30 | Année active + année précédente  |

---

## Données nominales générées

### Prénoms masculins
Jean, Pierre, Paul, Marc, Luc, David, Emmanuel, Samuel, Joseph, Daniel…

### Prénoms féminins
Marie, Sophie, Claire, Anne, Julie, Sarah, Esther, Ruth, Naomi, Rebecca…

### Noms de famille
Mutombo, Kabila, Nkosi, Lumumba, Kasongo, Ngoy, Mbuyi, Tshimanga…

---

## Scénarios de test

Le jeu de données permet de tester :

- **Pagination** : 55 élèves → vérifier que la liste paginée fonctionne correctement
- **Recherche** : recherche par nom, matricule, prénom
- **Filtres** : filtrer par statut, année, type de personnel
- **Inscriptions** : élèves avec historique sur plusieurs années
- **Multi-parents** : ~30% des élèves ont 2 contacts associés
- **Classes multiples** : S1 et S2 ont 2 classes par option → tester le changement de classe
- **Tables vides** : `Year 2022-2023` archivée, aucune inscription active → tester les empty states

---

## Réinitialisation

```bash
python manage.py reset_test_data --yes
```

Voir [reset-test-data.md](reset-test-data.md) pour la documentation complète.
