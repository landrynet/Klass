# Rapport de Configuration et de Lancement — KLASS

**Projet :** KLASS — Plateforme SaaS de Gestion Scolaire
**Université :** Don Bosco de Lubumbashi (UDBL)
**Document :** Procédure de déploiement et de lancement en développement

---

## Sommaire

1. [Configuration de la base de données PostgreSQL](#1-configuration-de-la-base-de-données-postgresql)
2. [Script principal de lancement](#2-script-principal-de-lancement)
3. [Lancement de l'application](#3-lancement-de-lapplication)
4. [Règle d'idempotence](#4-règle-didempotence)
5. [Documentation complémentaire](#5-documentation-complémentaire)

---

## 1. Configuration de la base de données PostgreSQL

### Objectif

Disposer d'un script dédié, fiable et réutilisable pour configurer PostgreSQL avant tout lancement du projet.

### Fichier concerné

```
klass/scripts/setup_db.sh
```

### Fonctionnalités assurées

| Vérification | Description |
|---|---|
| Installation | Vérifie que PostgreSQL est installé et que `psql` est accessible |
| Disponibilité | Vérifie que le serveur PostgreSQL est en cours d'exécution |
| Base de données | Crée la base si elle n'existe pas encore |
| Utilisateur | Crée l'utilisateur PostgreSQL si nécessaire |
| Droits | Accorde les droits complets sur la base à l'utilisateur |
| Connexion | Teste réellement la connexion avec les identifiants configurés |
| Erreurs | Affiche des messages d'erreur clairs en cas d'échec |
| Idempotence | Ne crée jamais de doublons si la base ou l'utilisateur existent déjà |

### Configuration par variables d'environnement

Tous les identifiants sont définis dans le fichier `.env`, jamais écrits en dur dans le code :

```env
POSTGRES_DB=klass
POSTGRES_USER=klass
POSTGRES_PASSWORD=
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

> **Règle de sécurité :** Le fichier `.env` ne doit jamais être commité dans le dépôt Git. Utiliser `.env.example` comme modèle public.

### Utilisation

```bash
bash scripts/setup_db.sh
```

---

## 2. Script principal de lancement

### Objectif

Fournir un point d'entrée unique permettant à tout développeur de préparer et lancer KLASS sans intervention manuelle sur chaque étape.

### Fichier concerné

```
klass/run.sh
```

### Étapes d'exécution

Le script enchaîne automatiquement les vérifications et actions suivantes :

---

#### Étape 1 — Vérification Git

Le script vérifie que le projet est connecté à un dépôt distant.

- Si un dépôt distant est configuré, il effectue un `git fetch` pour détecter les mises à jour disponibles.
- Il n'écrase jamais silencieusement les modifications locales.
- En cas de conflits détectés, le processus s'arrête avec un message explicite.

---

#### Étape 2 — Environnement Python

Le script détecte la version de Python disponible (3.11 minimum requis).

- Si le virtualenv `.venv` n'existe pas → il est créé automatiquement.
- S'il existe déjà → il est réutilisé tel quel.
- Le virtualenv est activé avant toute opération suivante.

---

#### Étape 3 — Dépendances Python

Installation ou mise à jour des bibliothèques depuis :

```
requirements/development.txt
```

- La commande `pip install` est exécutée avec vérification du résultat.
- En cas d'erreur, le script affiche la cause et s'arrête.

---

#### Étape 4 — Variables d'environnement

Le script vérifie la présence du fichier `.env`.

- S'il est absent, il est créé automatiquement depuis `.env.example`.
- Un avertissement invite à remplir les valeurs sensibles avant de continuer.
- Les variables obligatoires (`SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`) sont vérifiées explicitement.

---

#### Étape 5 — PostgreSQL

Le script contrôle la chaîne de connexion complète :

```
PostgreSQL installé
        ↓
PostgreSQL en fonctionnement (pg_isready)
        ↓
Base de données accessible
        ↓
Connexion Django → PostgreSQL réussie
```

Si une étape échoue, le script s'arrête et indique précisément le problème.

---

#### Étape 6 — Redis

Vérifications effectuées :

- Redis est accessible à l'URL configurée (`REDIS_URL`).
- La connexion est testée réellement (commande `PING`).

---

#### Étape 7 — Celery

Vérifications effectuées :

- Celery est installé et la version est affichée.
- Le broker Redis est accessible.

---

#### Étape 8 — Migrations

Les migrations sont **bloquantes** : toute erreur arrête le lancement.

```bash
python manage.py check
python manage.py makemigrations --check   # Détecte les migrations manquantes
python manage.py migrate_schemas --shared # Migrations du schéma public
python manage.py migrate_schemas          # Migrations de tous les tenants
```

Les migrations ne sont exécutées qu'après confirmation que la connexion à la base fonctionne.

---

#### Étape 9 — Fichiers statiques

```bash
python manage.py collectstatic --noinput
```

Exécuté uniquement en environnement de développement.

---

#### Étape 10 — Bilan de santé

Avant de démarrer l'application, un résumé complet est affiché :

```
[✓] Python
[✓] Environnement virtuel
[✓] Dépendances
[✓] Variables d'environnement
[✓] PostgreSQL
[✓] Base de données
[✓] Redis
[✓] Celery
[✓] Migrations
[✓] Django
```

En cas d'échec, le script identifie précisément l'étape concernée et arrête le processus.

### Options de lancement

```bash
bash run.sh                 # Lancement complet
bash run.sh --skip-git      # Ignorer la vérification Git
bash run.sh --skip-celery   # Ne pas démarrer Celery
```

---

## 3. Lancement de l'application

Une fois toutes les vérifications réussies, le script démarre les services suivants :

| Service | Mode | Logs |
|---|---|---|
| Celery Worker | Arrière-plan (détaché) | `/tmp/celery_worker.log` |
| Celery Beat | Arrière-plan (détaché) | `/tmp/celery_beat.log` |
| Serveur Django | Premier plan | Console |

### Avec Docker Compose

Les services disponibles via Docker :

```yaml
services:
  web      # Serveur Django
  db       # PostgreSQL
  redis    # Redis
  worker   # Celery Worker
  beat     # Celery Beat
```

```bash
cp .env.example .env
docker compose up
```

Le service est accessible sur `http://localhost:8000`.

---

## 4. Règle d'idempotence

> **Le script de lancement peut être exécuté plusieurs fois sans risque.**

Les garanties fournies :

| Ressource | Comportement |
|---|---|
| Base de données | Non recréée si elle existe déjà |
| Utilisateur PostgreSQL | Non recréé s'il existe déjà |
| Virtualenv Python | Non recréé s'il existe déjà |
| Migrations | Appliquées uniquement si nécessaire |
| Fichiers statiques | Écrasés proprement sans duplication |

---

## 5. Documentation complémentaire

Pour aller plus loin :

| Sujet | Fichier |
|---|---|
| Architecture générale | [`docs/architecture.md`](architecture.md) |
| Base de données & schémas | [`docs/database.md`](database.md) |
| Architecture multi-tenant | [`docs/multi-tenancy.md`](multi-tenancy.md) |
| Système de permissions | [`docs/permissions.md`](permissions.md) |
| Guide de développement | [`docs/development.md`](development.md) |
| Variables d'environnement | [`.env.example`](../.env.example) |

---

*Document généré dans le cadre du projet KLASS — UDBL.*
