#!/usr/bin/env bash
# =============================================================================
# KLASS — Script principal de lancement (Universel)
# Idempotent : peut être relancé sans risque.
# Usage : ./run.sh [--skip-git] [--skip-celery] [--skip-seed]
# =============================================================================
set -euo pipefail

# =============================================================================
# DÉTECTION DU SYSTÈME D'EXPLOITATION
# =============================================================================
detect_os() {
    case "$(uname -s)" in
        Linux*)     echo "linux" ;;
        Darwin*)    echo "macos" ;;
        CYGWIN*|MINGW*|MSYS*) echo "windows" ;;
        *)          echo "unknown" ;;
    esac
}

OS=$(detect_os)

# =============================================================================
# CONFIGURATION SPÉCIFIQUE PAR OS
# =============================================================================
configure_paths() {
    case "$OS" in
        windows)
            # Chemins PostgreSQL sur Windows
            for version in 18 17 16 15 14; do
                if [ -d "/c/Program Files/PostgreSQL/$version/bin" ]; then
                    export PATH="/c/Program Files/PostgreSQL/$version/bin:$PATH"
                    break
                fi
                if [ -d "/c/Program Files (x86)/PostgreSQL/$version/bin" ]; then
                    export PATH="/c/Program Files (x86)/PostgreSQL/$version/bin:$PATH"
                    break
                fi
            done
            ;;
        linux|macos)
            # Sur Linux/macOS, on utilise les chemins standards
            # PostgreSQL est généralement dans /usr/bin ou /usr/local/bin
            ;;
    esac
}

configure_paths

# =============================================================================
# FONCTION PYTHON UNIVERSEL
# =============================================================================
find_python() {
    # Ordre de priorité selon l'OS
    local python_candidates=()
    
    case "$OS" in
        windows)
            python_candidates=("py" "python3" "python")
            ;;
        linux|macos)
            python_candidates=("python3" "python" "py")
            ;;
    esac
    
    # Ajouter les versions spécifiques
    for version in 3.13 3.12 3.11 3.10; do
        python_candidates+=("python$version")
    done
    
    for py in "${python_candidates[@]}"; do
        if command -v "$py" &>/dev/null; then
            echo "$py"
            return 0
        fi
    done
    
    return 1
}

# =============================================================================
# COMMANDE PYTHON UNIVERSELLE
# =============================================================================
# Si 'python' n'existe pas sur Windows, on crée un alias
if [ "$OS" = "windows" ] && ! command -v python &>/dev/null; then
    python() {
        command py "$@"
    }
    export -f python
fi

# =============================================================================
# PARAMÈTRES
# =============================================================================
SKIP_GIT=false
SKIP_CELERY=false
SKIP_SEED=false
for arg in "$@"; do
    case "$arg" in
        --skip-git)    SKIP_GIT=true ;;
        --skip-celery) SKIP_CELERY=true ;;
        --skip-seed)   SKIP_SEED=true ;;
    esac
done

# =============================================================================
# COULEURS & HELPERS
# =============================================================================
if [ -t 1 ]; then
    # Terminal interactif - couleurs activées
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    CYAN='\033[0;36m'
    NC='\033[0m' # No Color
else
    # Non interactif - pas de couleurs
    RED=''; GREEN=''; YELLOW=''; BLUE=''; CYAN=''; NC=''
fi

ok()      { echo -e "${GREEN}[✓]${NC} $*"; }
warn()    { echo -e "${YELLOW}[!]${NC} $*"; }
fail()    { echo -e "${RED}[✗]${NC} $*"; exit 1; }
section() { echo -e "\n${BLUE}▶ $*${NC}"; }
info()    { echo -e "${CYAN}[i]${NC} $*"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Tableau de bord final
declare -A STATUS

# =============================================================================
# RÉSUMÉ FINAL
# =============================================================================
print_summary() {
    echo ""
    echo "══════════════════════════════════════════════"
    echo "  KLASS — Bilan du démarrage"
    echo "══════════════════════════════════════════════"
    echo "  OS détecté : $OS"
    echo ""
    for key in "Python" "Venv" "Dépendances" "Variables" "PostgreSQL" "Base" "Redis" "Celery" "Migrations" "Seed" "Django"; do
        val="${STATUS[$key]:-⬜ inconnu}"
        echo "  $val  $key"
    done
    echo ""
}

# =============================================================================
# ÉTAPE 1 — GIT
# =============================================================================
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

# =============================================================================
# ÉTAPE 2 — ENVIRONNEMENT PYTHON
# =============================================================================
section "Environnement Python"

PYTHON_BIN=$(find_python)
if [ -z "$PYTHON_BIN" ]; then
    fail "Python introuvable. Installez Python 3.11+."
fi

PY_VERSION=$("$PYTHON_BIN" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
MINOR=$(echo "$PY_VERSION" | cut -d. -f2)

if [ "$MAJOR" -lt 3 ] || { [ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 11 ]; }; then
    fail "Python 3.11+ requis, trouvé : $PY_VERSION"
fi
ok "Python $PY_VERSION ($PYTHON_BIN)"
STATUS["Python"]="✅"

# Environnement virtuel
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
    "$PYTHON_BIN" -m venv "$VENV_DIR"
    ok "Environnement virtuel créé"
else
    ok "Environnement virtuel déjà présent"
fi
STATUS["Venv"]="✅"

# Activation selon l'OS
if [ "$OS" = "windows" ] && [ -f "$VENV_DIR/Scripts/activate" ]; then
    # shellcheck disable=SC1091
    source "$VENV_DIR/Scripts/activate"
elif [ -f "$VENV_DIR/bin/activate" ]; then
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
else
    fail "Impossible d'activer l'environnement virtuel"
fi

# =============================================================================
# ÉTAPE 3 — DÉPENDANCES
# =============================================================================
section "Dépendances Python"

REQ_FILE=""
if [ -f "requirements/development.txt" ]; then
    REQ_FILE="requirements/development.txt"
elif [ -f "requirements/local.txt" ]; then
    REQ_FILE="requirements/local.txt"
elif [ -f "requirements.txt" ]; then
    REQ_FILE="requirements.txt"
else
    fail "Fichier requirements introuvable."
fi

python -m pip install --quiet --upgrade pip --no-user
if python -m pip install --quiet --no-user -r "$REQ_FILE"; then
    ok "Dépendances installées ($REQ_FILE)"
    STATUS["Dépendances"]="✅"
else
    STATUS["Dépendances"]="❌"
    fail "Erreur lors de l'installation des dépendances."
fi

# =============================================================================
# ÉTAPE 4 — VARIABLES D'ENVIRONNEMENT
# =============================================================================
section "Variables d'environnement"

# Charger .env (compatible tous OS)
set -a
if [ -f ".env" ]; then
    # Méthode universelle pour charger .env
    if command -v dos2unix &>/dev/null; then
        dos2unix .env 2>/dev/null || true
    fi
    # shellcheck disable=SC1090
    source ".env" 2>/dev/null || {
        # Fallback : lecture manuelle
        while IFS='=' read -r key value; do
            # Ignorer les commentaires et lignes vides
            if [[ ! -z "$key" && ! "$key" =~ ^# && "$key" =~ ^[A-Za-z_] ]]; then
                # Supprimer les guillemets et espaces
                value=$(echo "$value" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//;s/^"//;s/"$//')
                export "$key=$value"
            fi
        done < .env
    }
fi
set +a

if [ ! -f ".env" ]; then
    info "Aucun fichier .env : utilisation des variables d'environnement du système/Replit."
fi

# Vérifier les variables requises
REQUIRED_VARS=("SECRET_KEY" "DATABASE_URL")
MISSING=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var:-}" ]; then
        MISSING+=("$var")
    fi
done

if [ ${#MISSING[@]} -gt 0 ]; then
    STATUS["Variables"]="❌"
    fail "Variables obligatoires manquantes dans .env : ${MISSING[*]}"
fi
ok "Variables d'environnement présentes"
STATUS["Variables"]="✅"

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings.development}"

# =============================================================================
# ÉTAPE 5 — POSTGRESQL
# =============================================================================
section "PostgreSQL"

DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"

PG_AVAILABLE=false
PG_MESSAGE=""

# Test PostgreSQL selon l'OS
if command -v pg_isready &>/dev/null; then
    if pg_isready -h "$DB_HOST" -p "$DB_PORT" -q 2>/dev/null; then
        PG_AVAILABLE=true
    fi
elif command -v psql &>/dev/null; then
    if psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -c '\q' 2>/dev/null; then
        PG_AVAILABLE=true
    fi
fi

if [ "$PG_AVAILABLE" = true ]; then
    ok "PostgreSQL opérationnel sur $DB_HOST:$DB_PORT"
    STATUS["PostgreSQL"]="✅"
else
    STATUS["PostgreSQL"]="⚠️"
    warn "PostgreSQL ne répond pas sur $DB_HOST:$DB_PORT."
    case "$OS" in
        linux)   info "Démarrez PostgreSQL : sudo systemctl start postgresql" ;;
        macos)   info "Démarrez PostgreSQL : brew services start postgresql" ;;
        windows) info "Démarrez PostgreSQL : pg_ctl -D \"C:\\Program Files\\PostgreSQL\\18\\data\" start" ;;
    esac
fi

# Test de connexion Django
if python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', '$DJANGO_SETTINGS_MODULE')
try:
    django.setup()
    from django.db import connection
    connection.ensure_connection()
    print('ok')
except Exception as e:
    print('error:', str(e))
" 2>/dev/null | grep -q "ok"; then
    ok "Connexion Django → PostgreSQL OK"
    STATUS["Base"]="✅"
else
    STATUS["Base"]="⚠️"
    warn "Django ne peut pas se connecter à la base. Vérifiez DATABASE_URL dans .env."
    info "Pour créer la base :"
    echo "  psql -U postgres -c 'CREATE DATABASE klass;'"
    echo "  psql -U postgres -c \"CREATE USER klass WITH PASSWORD 'klass123';\""
    echo "  psql -U postgres -c 'GRANT ALL PRIVILEGES ON DATABASE klass TO klass;'"
fi

# =============================================================================
# ÉTAPE 6 — REDIS
# =============================================================================
section "Redis"

REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"

if command -v redis-cli &>/dev/null; then
    if redis-cli ping 2>/dev/null | grep -q "PONG"; then
        ok "Redis opérationnel ($REDIS_URL)"
        STATUS["Redis"]="✅"
    else
        STATUS["Redis"]="⚠️"
        warn "Redis ne répond pas."
        case "$OS" in
            linux)   info "Démarrez Redis : sudo systemctl start redis" ;;
            macos)   info "Démarrez Redis : brew services start redis" ;;
            windows) info "Redis optionnel sur Windows — ignorez si non utilisé" ;;
        esac
    fi
else
    STATUS["Redis"]="⚠️"
    warn "Redis non installé ou non trouvé. (Optionnel)"
fi

# =============================================================================
# ÉTAPE 7 — CELERY
# =============================================================================
section "Celery"

if python -c "import celery" 2>/dev/null; then
    CELERY_VERSION=$(python -c "import celery; print(celery.__version__)" 2>/dev/null || echo "inconnue")
    ok "Celery installé (version $CELERY_VERSION)"
    STATUS["Celery"]="✅"
else
    STATUS["Celery"]="⚠️"
    warn "Celery non disponible. (Optionnel)"
fi

# =============================================================================
# ÉTAPE 8 — MIGRATIONS
# =============================================================================
section "Migrations Django"

# Check Django
if python manage.py check &>/dev/null; then
    ok "Vérification Django OK"
else
    warn "Django check a échoué — migrations possibles malgré tout"
fi

# Vérification des migrations manquantes
if python manage.py makemigrations --check --dry-run &>/dev/null; then
    ok "Aucune migration manquante détectée"
else
    warn "Des migrations non générées ont été détectées"
    if python manage.py makemigrations 2>/dev/null; then
        ok "Migrations générées automatiquement"
    else
        warn "makemigrations a échoué — à exécuter manuellement"
    fi
fi

# Migration (avec fallback)
MIGRATION_SUCCESS=false
if python manage.py migrate_schemas --shared --run-syncdb 2>/dev/null; then
    ok "Migrations schéma public appliquées"
    if python manage.py migrate_schemas 2>/dev/null; then
        ok "Migrations tenants appliquées"
        MIGRATION_SUCCESS=true
    fi
fi

if [ "$MIGRATION_SUCCESS" = false ]; then
    # Fallback : migration standard
    if python manage.py migrate 2>/dev/null; then
        ok "Migrations standard appliquées"
        MIGRATION_SUCCESS=true
    fi
fi

if [ "$MIGRATION_SUCCESS" = true ]; then
    STATUS["Migrations"]="✅"
else
    STATUS["Migrations"]="⚠️"
    warn "Migrations échouées — vous devrez les exécuter manuellement"
    info "Exécutez : python manage.py makemigrations && python manage.py migrate"
fi

# =============================================================================
# ÉTAPE 9 — DONNÉES DE DÉMONSTRATION
# =============================================================================
if [ "$SKIP_SEED" = false ]; then
    section "Données de démonstration"
    if python scripts/seed_data.py; then
        ok "Données de test créées/vérifiées (idempotent)"
        STATUS["Seed"]="✅"
    else
        STATUS["Seed"]="❌"
        fail "Le seed des données de test a échoué."
    fi
else
    STATUS["Seed"]="⏭️"
    info "Seed ignoré (--skip-seed)"
fi

# =============================================================================
# ÉTAPE 10 — FICHIERS STATIQUES
# =============================================================================
section "Fichiers statiques"
if python manage.py collectstatic --noinput --clear -v 0 2>/dev/null; then
    ok "Fichiers statiques collectés"
else
    warn "collectstatic échoué (non bloquant)"
fi

# =============================================================================
# ÉTAPE 11 — SANTÉ GLOBALE
# =============================================================================
section "Tests de santé"

if python manage.py check &>/dev/null; then
    ok "Django check OK"
    STATUS["Django"]="✅"
else
    STATUS["Django"]="⚠️"
    warn "Django check a échoué mais l'application peut fonctionner"
fi

print_summary

# =============================================================================
# LANCEMENT
# =============================================================================
section "Lancement des services KLASS"

PORT="${PORT:-8000}"

if [ "$SKIP_CELERY" = false ] && [ "${STATUS["Celery"]}" = "✅" ]; then
    # Celery Worker (en arrière-plan)
    if celery -A config.celery worker --loglevel=info --detach \
        --logfile=/tmp/celery_worker.log --pidfile=/tmp/celery_worker.pid 2>/dev/null; then
        ok "Celery Worker démarré (logs : /tmp/celery_worker.log)"
    else
        warn "Celery Worker non démarré (optionnel)"
    fi

    # Celery Beat (en arrière-plan)
    if celery -A config.celery beat --loglevel=info --detach \
        --logfile=/tmp/celery_beat.log --pidfile=/tmp/celery_beat.pid \
        --scheduler django_celery_beat.schedulers:DatabaseScheduler 2>/dev/null; then
        ok "Celery Beat démarré (logs : /tmp/celery_beat.log)"
    else
        warn "Celery Beat non démarré (optionnel)"
    fi
fi

# Afficher l'URL d'accès
echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}  🚀 KLASS est prêt → http://localhost:$PORT${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""
echo "💡 Pour arrêter : Ctrl+C"
echo "📋 Logs : /tmp/celery_*.log (si Celery actif)"
echo ""

# Serveur Django (foreground)
exec python manage.py runserver "0.0.0.0:$PORT"