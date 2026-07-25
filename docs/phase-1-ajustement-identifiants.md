# Ajustement Phase 1 — Informations d'accès de l'Admin École

## Contexte

Après création d'une école par le Super Admin, le système affiche désormais
les identifiants de l'Admin École sur une **page de confirmation dédiée**,
accessible **une seule fois** immédiatement après la création.

## Flux mis à jour

```
Super Admin crée l'école
    ↓  POST /super-admin/schools/create/
École + tenant PostgreSQL + Admin École créés
    ↓
Identifiants stockés en session (une seule lecture autorisée)
    ↓  Redirect
Page de confirmation /super-admin/schools/creation-success/
    ↓
Identifiants lus depuis la session puis effacés immédiatement
    ↓
Super Admin copie / transmet les identifiants à l'Admin École
    ↓  /auth/login/
Admin École : première connexion → changement obligatoire du mot de passe
    ↓
Assistant de configuration en 3 étapes
    ↓  /academics/
Dashboard de l'école (opérationnelle)
```

## Page de confirmation (`creation_success.html`)

### Ce qui est affiché

| Champ | Valeur |
|-------|--------|
| Nom de l'école | `school.name` |
| Nom complet de l'Admin | `admin_user.get_full_name()` |
| Email de connexion | `admin_user.email` |
| Mot de passe temporaire | généré par `generate_temp_password()` |
| Lien de connexion | `https://<slug>.klass.app/auth/login/` |

### Fonctionnalités UX

- **Copie individuelle** : bouton "Copier" pour chaque champ (Clipboard API avec fallback)
- **Copie globale** : "Copier tous les identifiants" génère un bloc texte formaté
- **Affichage unique** : la session est effacée dès le premier accès — toute visite
  ultérieure redirige vers le dashboard avec un message d'information
- **Prochaines étapes** : guide visuel en 3 points pour orienter le Super Admin

### Sécurité

- Le mot de passe temporaire n'est **jamais stocké en clair** dans la base de données.
- Il transite uniquement via la session Django (serveur-side, HTTPOnly).
- La session est effacée (`session.pop`) dès la première lecture de la page.
- Le Super Admin **ne peut pas** revoir le mot de passe après avoir quitté la page.

## Améliorations design

La page de création (`create.html`) a été redessinée :

- En-têtes de section avec icône + description
- Prévisualisation du sous-domaine en temps réel (slug calculé côté client)
- Panneau d'information latéral fixe (sticky) avec checklist et flux
- Spinner sur le bouton de soumission pour éviter les doubles clics
- Formulaire désactivé pendant la soumission
- Meilleure hiérarchie visuelle, espacements et typographie

## Fichiers modifiés

| Fichier | Modification |
|---------|-------------|
| `apps/tenants/views.py` | `SchoolCreateView.post` → session + redirect ; nouvelle `SchoolCreationSuccessView` |
| `apps/tenants/urls.py` | Ajout de `schools/creation-success/` |
| `templates/tenants/schools/create.html` | Redesign complet |
| `templates/tenants/schools/creation_success.html` | Nouveau template |
| `config/settings/development.py` | `CSRF_TRUSTED_ORIGINS` pour le domaine Replit |

## Tests

Tous les **50 tests existants** de la Phase 1 passent sans régression.

Vérifications manuelles effectuées :
- ✅ Création d'école → redirect vers la page de confirmation
- ✅ Identifiants affichés (nom école, email admin, mot de passe, lien)
- ✅ Deuxième visite → redirect dashboard (affichage unique confirmé)
- ✅ Page sans credentials en session → redirect avec message d'information
- ✅ Formulaire de création avec prévisualisation slug
