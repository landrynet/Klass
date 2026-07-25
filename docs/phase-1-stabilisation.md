# Stabilisation de la Phase 1

## État final

**PHASE 1 — STABILISÉE ET VALIDÉE**

Cette validation couvre le socle livré de la Phase 1 : création d'une école,
tenant PostgreSQL, compte Admin École, première connexion, changement de mot de
passe, assistant de configuration et permissions de base.

## Audit

Les éléments suivants ont été comparés au code réellement présent :

- documentation projet et architecture (`README.md`, `docs/`, document projet) ;
- applications Django, modèles et migrations ;
- services, formulaires, vues et URLs ;
- middleware de tenant, changement de mot de passe et configuration initiale ;
- templates de connexion, assistant et dashboards ;
- JavaScript, CSS et configuration d'environnement ;
- tests globaux et tests de Phase 1.

## Corrections réalisées

1. Les dépendances déclarées dans `requirements/development.txt` et
   `pyproject.toml` sont installées dans l'environnement du projet.
2. Les tests de vues utilisent correctement le schéma public lorsque la
   requête de test n'a pas de sous-domaine tenant.
3. Le helper de test de création d'école accepte correctement les noms
   d'administrateur personnalisés.
4. La création d'école ne place plus le mot de passe temporaire dans un
   message de redirection réaffichable. Le compte est signalé comme créé et
   les identifiants doivent être transmis par un canal sécurisé.
5. La documentation de développement précise la règle de non-exposition des
   mots de passe temporaires.

## Tests et contrôles exécutés

| Contrôle | Résultat |
|---|---|
| `python manage.py check` | OK |
| `python manage.py makemigrations --check --dry-run` | OK, aucune migration manquante |
| `pytest -q` | OK — 83 tests réussis |
| Migrations de la base de test | OK |
| Isolation et permissions Phase 1 | OK dans les tests dédiés |

## Sécurité vérifiée

- accès anonyme aux routes protégées : redirection vers la connexion ;
- accès d'un rôle école aux routes Super Admin : refusé ;
- accès d'un Super Admin à l'assistant école : refusé ;
- obligation de changement du mot de passe temporaire ;
- blocage d'un dashboard d'école avant configuration ;
- rattachement d'un compte à une seule école ;
- noms de schémas distincts pour deux écoles ;
- aucun mot de passe temporaire dans le message de succès de création.
- les sorties du script de démonstration n'affichent ni email ni mot de passe ;
  les données de démonstration utilisent un mot de passe généré par défaut.

La séparation PostgreSQL par schéma reste la garantie d'isolation en
production. Les vérifications locales de bout en bout avec plusieurs hôtes
tenant nécessitent une base PostgreSQL de test disposant de la résolution
DNS/sous-domaines correspondante.

## UX/UI et décisions de design

Les écrans existants suivent une direction produit cohérente : interface
française, hiérarchie claire, cartes à faible densité, progression visible sur
les trois étapes, champs responsifs Bootstrap et messages d'erreur côté
serveur. La connexion et l'assistant privilégient une action principale
unique, une largeur lisible sur mobile et des libellés explicites.

Les références étudiées pour la suite sont les patterns publics de SaaS
multi-tenant, dashboards d'administration et onboarding progressif. Les
principes retenus sont : progression persistante, validation progressive,
états d'erreur lisibles, action primaire unique et séparation stricte des
espaces d'administration.

## Documentation

La documentation de lancement et de développement reste la référence
opérationnelle. Ce rapport centralise l'état réel de la stabilisation.

## Préparation de la Phase 2

Les modèles `SchoolYear` et `academics` fournissent le point d'ancrage pour
la structure académique. La Phase 2 doit ajouter les écrans métier pour les
niveaux, options, classes et salles en conservant :

- une année scolaire active par tenant ;
- les modèles métier dans `TENANT_APPS` ;
- les permissions côté serveur ;
- des listes filtrées par tenant et année ;
- des formulaires validés côté serveur ;
- des états vides, chargement et erreur réutilisables.

Le développement métier complet de la Phase 2 n'est pas inclus dans cette
stabilisation.

## Limites restantes

- La transmission automatisée des identifiants par email n'est pas activée ;
  elle nécessite une configuration SMTP.
- Les notifications SMS/WhatsApp, abonnements et intégrations externes restent
  hors de la Phase 1.
- Les tests des flux de production multi-hôtes, sauvegarde/restauration et
  monitoring réel nécessitent les services d'exploitation correspondants.