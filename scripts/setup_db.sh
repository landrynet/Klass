#!/usr/bin/env bash
# =============================================================================
# KLASS — Script de configuration PostgreSQL
# Idempotent : peut être relancé sans risque de doublons.
# =============================================================================
set -euo pipefail

# ---------------------------------------------------------------------------
# Couleurs
# ---------------------------------------------------------------------------
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}[✓]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
fail() { echo -e "${RED}[✗]${NC} $*"; exit 1; }

# ---------------------------------------------------------------------------
# Charger .env
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$ROOT_DIR/.env"

if [ -f "$ENV_FILE" ]; then
    set -a; source "$ENV_FILE"; set +a
    ok "Variables chargées depuis .env"
else
    warn ".env introuvable — utilisation des valeurs par défaut"
fi

DB_NAME="${POSTGRES_DB:-klass}"
DB_USER="${POSTGRES_USER:-klass}"
DB_PASS="${POSTGRES_PASSWORD:-klass}"
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"

echo ""
echo "══════════════════════════════════════════"
echo "  Configuration PostgreSQL pour KLASS"
echo "══════════════════════════════════════════"
echo "  Hôte     : $DB_HOST:$DB_PORT"
echo "  Base     : $DB_NAME"
echo "  Utilisateur : $DB_USER"
echo ""

# ---------------------------------------------------------------------------
# 1. Vérifier que PostgreSQL est installé
# ---------------------------------------------------------------------------
if ! command -v psql &>/dev/null; then
    fail "psql introuvable. Installez PostgreSQL 14+ avant de continuer."
fi
ok "psql disponible : $(psql --version | head -1)"

# ---------------------------------------------------------------------------
# 2. Vérifier que le serveur PostgreSQL tourne
# ---------------------------------------------------------------------------
if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -q 2>/dev/null; then
    fail "PostgreSQL ne répond pas sur $DB_HOST:$DB_PORT. Démarrez le service."
fi
ok "PostgreSQL opérationnel sur $DB_HOST:$DB_PORT"

# ---------------------------------------------------------------------------
# 3. Créer l'utilisateur si nécessaire
# ---------------------------------------------------------------------------
USER_EXISTS=$(psql -h "$DB_HOST" -p "$DB_PORT" -U postgres \
    -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER';" 2>/dev/null || echo "")

if [ "$USER_EXISTS" = "1" ]; then
    ok "Utilisateur '$DB_USER' déjà existant"
else
    psql -h "$DB_HOST" -p "$DB_PORT" -U postgres \
        -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';" &>/dev/null
    ok "Utilisateur '$DB_USER' créé"
fi

# ---------------------------------------------------------------------------
# 4. Créer la base de données si nécessaire
# ---------------------------------------------------------------------------
DB_EXISTS=$(psql -h "$DB_HOST" -p "$DB_PORT" -U postgres \
    -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME';" 2>/dev/null || echo "")

if [ "$DB_EXISTS" = "1" ]; then
    ok "Base de données '$DB_NAME' déjà existante"
else
    psql -h "$DB_HOST" -p "$DB_PORT" -U postgres \
        -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" &>/dev/null
    ok "Base de données '$DB_NAME' créée"
fi

# ---------------------------------------------------------------------------
# 5. Accorder les droits
# ---------------------------------------------------------------------------
psql -h "$DB_HOST" -p "$DB_PORT" -U postgres \
    -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" &>/dev/null
ok "Droits accordés à '$DB_USER' sur '$DB_NAME'"

# ---------------------------------------------------------------------------
# 6. Tester la connexion avec les identifiants de l'application
# ---------------------------------------------------------------------------
if PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" \
    -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" &>/dev/null; then
    ok "Connexion Django → PostgreSQL vérifiée"
else
    fail "Impossible de se connecter avec les identifiants configurés. Vérifiez .env"
fi

echo ""
ok "Configuration PostgreSQL terminée avec succès."
