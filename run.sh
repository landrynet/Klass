#!/usr/bin/env bash
# =============================================================================
# KLASS — Script principal de lancement
# Idempotent : peut être relancé sans risque.
# Usage : ./run.sh [--skip-git] [--skip-celery]
# =============================================================================
set -euo pipefail

SKIP_GIT=false
SKIP_CELERY=false
for arg in "$@"; do
    case "$arg" in
        --skip-git)    SKIP_GIT=true ;;
        --skip-celery) SKIP_CELERY=true ;;
    esac
done

# ---------------------------------------------------------------------------
# Couleurs & helpers
# ---------------------------------------------------------------------------
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
ok()      { echo -e "${GREEN}[✓]${NC} $*"; }
warn()    { echo -e "${YELLOW}[!]${NC} $*"; }
fail()    { echo -e "${RED}[✗]${NC} $*"; exit 1; }
section() { echo -e "\n${BLUE}▶ $*${NC}"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Tableau de bord final
declare -A STATUS

# ---------------------------------------------------------------------------
# Étape 0 — Résumé
# ---------------------------------------------------------------------------
print_summary() {
    echo ""
    echo "══════════════════════════════════════════════"
    echo "  KLASS — Bilan du démarrage"
    echo "══════════════════════════════════════════════"
    for key in "Python" "Venv" "Dépendances" "Variables" "PostgreSQL" "Base" "Redis" "Celery" "Migrations" "Django"; do
        val="${STATUS[$key]:-⬜ inconnu}"
        echo "  $val  $key"
    done
    echo ""
}

# ---------------------------------------------------------------------------
# Étape 1 — Git
# ---------------------------------------------------------------------------
if [ "$SKIP_GIT" = false ] && git rev-parse --git-dir &>/dev/null; then
    section "Vérification Git"
    REMOTE=$(git remote 2>/dev/null | head -1)
    if [ -n "$REMOTE" ]; then
        git fetch "$REMOTE" --quiet 2>/dev/null || warn "Impossible de joindre le dépôt distant"
        LOCAL=$(git rev-parse HEAD)
        UPSTREAM=$(git rev-parse "@{u}" 2>/dev/null || echo "$LOCAL")
        if [ "$LOCAL" != "$UPSTREAM" ]; then
            warn "Des mises à jour sont disponibles sur le dépôt distant."
            warn "Lancez 'git pull' manuellement pour les appliquer."
        else
            ok "Dépôt à jour"
        fi
    else
        warn "Pas de dépôt distant configuré — étape Git ignorée"
    fi
fi

# ---------------------------------------------------------------------------
# Étape 2 — Environnement Python
# ---------------------------------------------------------------------------
section "Environnement Python"

PYTHON_BIN=""
for py in python3.13 python3.12 python3.11 python3 python; do
    if command -v "$py" &>/dev/null; then
        PYTHON_BIN="$py"
        break
    fi
done
[ -z "$PYTHON_BIN" ] && fail "Python introuvable. Installez Python 3.11+."

PY_VERSION=$("$PYTHON_BIN" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
if [ "$MAJOR" -lt 3 ] || { [ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 11 ]; }; then
    fail "Python 3.11+ requis, trouvé : $PY_VERSION"
fi
ok "Python $PY_VERSION ($PYTHON_BIN)"
STATUS["Python"]="✅"

VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
    "$PYTHON_BIN" -m venv "$VENV_DIR"
    ok "Environnement virtuel créé"
else
    ok "Environnement virtuel déjà présent"
fi
STATUS["Venv"]="✅"

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# ---------------------------------------------------------------------------
# Étape 3 — Dépendances
# ---------------------------------------------------------------------------
section "Dépendances Python"

REQ_FILE="requirements/development.txt"
[ ! -f "$REQ_FILE" ] && REQ_FILE="requirements.txt"
[ ! -f "$REQ_FILE" ] && fail "Fichier requirements introuvable."

pip install --quiet --upgrade pip
if pip install --quiet -r "$REQ_FILE"; then
    ok "Dépendances installées ($REQ_FILE)"
    STATUS["Dépendances"]="✅"
else
    STATUS["Dépendances"]="❌"
    fail "Erreur lors de l'installation des dépendances."
fi

# ---------------------------------------------------------------------------
# Étape 4 — Variables d'environnement
# ---------------------------------------------------------------------------
section "Variables d'environnement"

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        warn ".env créé depuis .env.example — remplissez les valeurs sensibles avant de continuer."
    else
        fail ".env manquant et .env.example introuvable."
    fi
fi

set -a; source ".env"; set +a

REQUIRED_VARS=("SECRET_KEY" "DATABASE_URL" "REDIS_URL")
MISSING=()
for var in "${REQUIRED_VARS[@]}"; do
    [ -z "${!var:-}" ] && MISSING+=("$var")
done

if [ ${#MISSING[@]} -gt 0 ]; then
    STATUS["Variables"]="❌"
    fail "Variables obligatoires manquantes dans .env : ${MISSING[*]}"
fi
ok "Variables d'environnement présentes"
STATUS["Variables"]="✅"

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings.development}"

# ---------------------------------------------------------------------------
# Étape 5 — PostgreSQL
# ---------------------------------------------------------------------------
section "PostgreSQL"

DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"

if ! command -v pg_isready &>/dev/null; then
    STATUS["PostgreSQL"]="⚠️"
    warn "pg_isready introuvable — vérification PostgreSQL ignorée"
elif ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -q 2>/dev/null; then
    STATUS["PostgreSQL"]="❌"
    fail "PostgreSQL ne répond pas sur $DB_HOST:$DB_PORT. Lancez 'scripts/setup_db.sh' d'abord."
else
    ok "PostgreSQL opérationnel"
    STATUS["PostgreSQL"]="✅"
fi

if python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', '$DJANGO_SETTINGS_MODULE')
django.setup()
from django.db import connection
connection.ensure_connection()
print('ok')
" 2>/dev/null | grep -q "ok"; then
    ok "Connexion Django → PostgreSQL OK"
    STATUS["Base"]="✅"
else
    STATUS["Base"]="❌"
    fail "Django ne peut pas se connecter à la base. Vérifiez DATABASE_URL dans .env."
fi

# ---------------------------------------------------------------------------
# Étape 6 — Redis
# ---------------------------------------------------------------------------
section "Redis"

REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"

if python -c "
import redis
r = redis.from_url('$REDIS_URL', socket_connect_timeout=3)
r.ping()
print('ok')
" 2>/dev/null | grep -q "ok"; then
    ok "Redis opérationnel ($REDIS_URL)"
    STATUS["Redis"]="✅"
else
    STATUS["Redis"]="❌"
    fail "Redis inaccessible à $REDIS_URL. Démarrez Redis avant de continuer."
fi

# ---------------------------------------------------------------------------
# Étape 7 — Celery
# ---------------------------------------------------------------------------
section "Celery"

if python -c "import celery; print('ok')" 2>/dev/null | grep -q "ok"; then
    ok "Celery installé ($(python -c 'import celery; print(celery.__version__)'))"
    STATUS["Celery"]="✅"
else
    STATUS["Celery"]="❌"
    warn "Celery non disponible."
fi

# ---------------------------------------------------------------------------
# Étape 8 — Migrations
# ---------------------------------------------------------------------------
section "Migrations Django"

python manage.py check && ok "Vérification Django OK" || { fail "Django check a échoué."; }

# Vérifier qu'aucune migration n'a été oubliée
if python manage.py makemigrations --check --dry-run &>/dev/null; then
    ok "Aucune migration manquante détectée"
else
    warn "Des migrations non générées ont été détectées — lancez 'python manage.py makemigrations' puis relancez."
fi

if python manage.py migrate_schemas --shared --run-syncdb; then
    ok "Migrations schéma public appliquées"
else
    STATUS["Migrations"]="❌"
    print_summary
    fail "migrate_schemas --shared a échoué. Vérifiez la connexion à la base et les modèles."
fi

if python manage.py migrate_schemas; then
    ok "Migrations tenants appliquées"
    STATUS["Migrations"]="✅"
else
    STATUS["Migrations"]="❌"
    print_summary
    fail "migrate_schemas a échoué. Vérifiez les migrations de chaque application tenant."
fi

# ---------------------------------------------------------------------------
# Étape 9 — Fichiers statiques
# ---------------------------------------------------------------------------
section "Fichiers statiques"
python manage.py collectstatic --noinput --clear -v 0 2>/dev/null && ok "Fichiers statiques collectés" || warn "collectstatic échoué (non bloquant)"

# ---------------------------------------------------------------------------
# Étape 10 — Santé globale
# ---------------------------------------------------------------------------
section "Tests de santé"

python manage.py check && ok "Django check OK" || fail "Django check a échoué."
STATUS["Django"]="✅"

print_summary

# ---------------------------------------------------------------------------
# Lancement
# ---------------------------------------------------------------------------
section "Lancement des services KLASS"

PORT="${PORT:-8000}"

if [ "$SKIP_CELERY" = false ]; then
    # Celery Worker en arrière-plan
    celery -A config.celery worker --loglevel=info --detach \
        --logfile=/tmp/celery_worker.log --pidfile=/tmp/celery_worker.pid 2>/dev/null && \
        ok "Celery Worker démarré (logs : /tmp/celery_worker.log)" || \
        warn "Celery Worker n'a pas démarré (non bloquant)"

    # Celery Beat en arrière-plan
    celery -A config.celery beat --loglevel=info --detach \
        --logfile=/tmp/celery_beat.log --pidfile=/tmp/celery_beat.pid \
        --scheduler django_celery_beat.schedulers:DatabaseScheduler 2>/dev/null && \
        ok "Celery Beat démarré (logs : /tmp/celery_beat.log)" || \
        warn "Celery Beat n'a pas démarré (non bloquant)"
fi

echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}  KLASS est prêt → http://localhost:$PORT${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""

# Serveur Django (foreground)
exec python manage.py runserver "0.0.0.0:$PORT"
