#!/bin/bash

# =============================================================================
# ZaraiLink Setup Script for Linux (Ubuntu 22.04 / 24.04)
# =============================================================================
# Automates the complete setup of the ZaraiLink development environment.
# Idempotent — safe to run multiple times.
#
# Prerequisites:
#   - Python 3.12+
#   - Node.js 18+ and npm
#   - Docker (with Compose plugin or docker-compose)
#   - PostgreSQL 15+
#
# Usage:
#   chmod +x setup_linux.sh
#   ./setup_linux.sh
# =============================================================================

set -e  # Exit immediately on any error

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

print_header() { echo ""; echo -e "${BLUE}══════════════════════════════════════════════════════════════════${NC}"; echo -e "${BOLD}${CYAN}  $1${NC}"; echo -e "${BLUE}══════════════════════════════════════════════════════════════════${NC}"; }
print_step()   { echo -e "${GREEN}[✓]${NC} $1"; }
print_skip()   { echo -e "${YELLOW}[⊘]${NC} $1 ${YELLOW}(already done, skipping)${NC}"; }
print_info()   { echo -e "${CYAN}[i]${NC} $1"; }
print_warn()   { echo -e "${YELLOW}[!]${NC} $1"; }
print_error()  { echo -e "${RED}[✗]${NC} $1" >&2; }

# ── Docker Compose helper ─────────────────────────────────────────────────────
docker_compose() {
    if docker compose version &>/dev/null 2>&1; then
        docker compose "$@"
    elif command -v docker-compose &>/dev/null; then
        docker-compose "$@"
    else
        print_error "Neither 'docker compose' nor 'docker-compose' is available."
        print_error "Install: https://docs.docker.com/compose/install/"
        exit 1
    fi
}

# =============================================================================
# PRE-FLIGHT CHECKS
# =============================================================================
print_header "PRE-FLIGHT CHECKS"

# Python 3.12+
if ! command -v python3 &>/dev/null; then
    print_error "Python 3 is not installed."
    echo -e "${YELLOW}  sudo apt install python3 python3-venv python3-pip${NC}"
    exit 1
fi
PYTHON_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_MAJOR=$(echo $PYTHON_VER | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VER | cut -d. -f2)
if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 12 ]; }; then
    print_error "Python 3.12+ required. Found: $PYTHON_VER"
    echo -e "${YELLOW}  sudo apt install python3.12 python3.12-venv${NC}"
    exit 1
fi
print_step "Python $PYTHON_VER"

# python3-venv
if ! python3 -m venv --help &>/dev/null; then
    print_error "python3-venv missing."
    echo -e "${YELLOW}  sudo apt install python3-venv${NC}"
    exit 1
fi
print_step "python3-venv available"

# Node.js 18+
if ! command -v node &>/dev/null; then
    print_error "Node.js is not installed."
    echo -e "${YELLOW}  curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -${NC}"
    echo -e "${YELLOW}  sudo apt install -y nodejs${NC}"
    exit 1
fi
NODE_VER=$(node --version)
print_step "Node.js $NODE_VER"

# npm
if ! command -v npm &>/dev/null; then
    print_error "npm is not installed (should come with Node.js)."
    exit 1
fi
print_step "npm $(npm --version)"

# Docker
if ! command -v docker &>/dev/null; then
    print_error "Docker is not installed."
    echo -e "${YELLOW}  https://docs.docker.com/engine/install/ubuntu/${NC}"
    exit 1
fi
if ! docker info &>/dev/null 2>&1; then
    print_error "Docker is not running or you lack permission."
    echo -e "${YELLOW}  sudo systemctl start docker${NC}"
    echo -e "${YELLOW}  sudo usermod -aG docker \$USER  (then log out & back in)${NC}"
    exit 1
fi
print_step "Docker running"

# PostgreSQL
if ! command -v psql &>/dev/null; then
    print_error "PostgreSQL client (psql) not found."
    echo -e "${YELLOW}  sudo apt install postgresql postgresql-contrib${NC}"
    exit 1
fi
if ! systemctl is-active --quiet postgresql 2>/dev/null; then
    print_info "Starting PostgreSQL service..."
    sudo systemctl start postgresql
fi
print_step "PostgreSQL running"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
print_step "Working directory: $SCRIPT_DIR"

# =============================================================================
# BACKEND SETUP
# =============================================================================
print_header "BACKEND SETUP"

cd "$SCRIPT_DIR/backend"

# Virtual environment — recreate if broken
if [ -d ".venv" ] && { [ ! -f ".venv/bin/activate" ] || [ ! -f ".venv/bin/pip" ]; }; then
    print_warn "Existing .venv appears broken — recreating..."
    rm -rf .venv
fi

if [ ! -d ".venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv .venv || { print_error "Failed to create venv. Try: sudo apt install python3-venv"; exit 1; }
    print_step "Virtual environment created"
else
    print_skip "Virtual environment"
fi

source .venv/bin/activate
[ -z "$VIRTUAL_ENV" ] && { print_error "Failed to activate venv!"; exit 1; }
print_step "Virtual environment activated: $VIRTUAL_ENV"

# Python dependencies — always run to catch new packages
print_info "Installing/updating Python dependencies..."
.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install -r requirements.txt -q
for pkg in django numpy pandas openpyxl sentence_transformers lightgbm; do
    .venv/bin/pip show "$pkg" &>/dev/null || { print_error "Failed to install $pkg!"; exit 1; }
done
print_step "Python dependencies installed"

# .env file
if [ ! -f ".env" ]; then
    print_info "Creating .env from .env.example..."
    [ ! -f ".env.example" ] && { print_error ".env.example not found!"; exit 1; }
    cp .env.example .env
    SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
    sed -i "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|g" .env
    print_step ".env created with generated SECRET_KEY"
else
    print_skip ".env file"
fi

# =============================================================================
# DATABASE SETUP
# =============================================================================
print_header "DATABASE SETUP"

# Create database if it doesn't exist
if sudo -u postgres psql -lqt 2>/dev/null | cut -d\| -f1 | grep -qw zarailink; then
    print_skip "Database 'zarailink'"
else
    print_info "Creating PostgreSQL database and user..."
    sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';" 2>/dev/null || true
    sudo -u postgres createdb zarailink || { print_error "Failed to create database. Run: sudo -u postgres createdb zarailink"; exit 1; }
    print_step "Database 'zarailink' created"
fi

# Run all pending migrations (including new search + trade_data migrations)
print_info "Running database migrations..."
python manage.py migrate --no-input
print_step "Migrations complete"

# Setup company roles (idempotent)
print_info "Setting up company roles..."
python manage.py setup_company_roles
print_step "Company roles configured"

# Sample company data
if python manage.py shell -c "from companies.models import Company; exit(0 if Company.objects.exists() else 1)" 2>/dev/null; then
    print_skip "Sample company data"
else
    if [ -f "load_data.py" ]; then
        print_info "Loading sample company data..."
        python load_data.py && print_step "Sample company data loaded"
    else
        print_info "No load_data.py — skipping sample data"
    fi
fi

# Trade data import
if python manage.py shell -c "from trade_data.models import Transaction; exit(0 if Transaction.objects.exists() else 1)" 2>/dev/null; then
    print_skip "Trade transaction data"
else
    if [ -f "../import_data_1year.xlsx" ]; then
        print_info "Importing trade data (may take several minutes)..."
        python manage.py ingest_trade --file ../import_data_1year.xlsx \
            && print_step "Trade data imported" \
            || print_warn "Trade data import failed — search will return empty results"
    else
        print_warn "import_data_1year.xlsx not found. Place it at: $SCRIPT_DIR/import_data_1year.xlsx"
        print_warn "Search will return empty results until trade data is imported."
    fi
fi

# GNN graphs
TX_COUNT=$(python manage.py shell -c "from trade_data.models import Transaction; print(Transaction.objects.count())" 2>/dev/null || echo "0")
if [ "$TX_COUNT" -gt 0 ] 2>/dev/null; then
    if [ ! -f "company_product_graph.graphml" ]; then
        print_info "Building GNN trade graphs..."
        python manage.py build_gnn_graphs \
            && print_step "GNN graphs built" \
            || print_warn "GNN graph build failed (optional — Similar Companies feature affected)"
    else
        print_skip "GNN graphs"
    fi

    # GNN embeddings
    if python manage.py shell -c "from trade_data.models import CompanyEmbedding; exit(0 if CompanyEmbedding.objects.exists() else 1)" 2>/dev/null; then
        print_skip "GNN embeddings"
    else
        if [ -f "company_product_graph.graphml" ]; then
            print_info "Generating GNN embeddings (may take several minutes)..."
            python manage.py generate_gnn_embeddings --fast \
                && print_step "GNN embeddings generated" \
                || print_warn "GNN embedding generation failed (optional)"
        fi
    fi
fi

# =============================================================================
# OPENSEARCH SETUP (required for search)
# =============================================================================
print_header "OPENSEARCH SETUP"

OPENSEARCH_OK=false
if curl -s --connect-timeout 3 "http://localhost:9200" | grep -q '"status" : 200\|"tagline"' 2>/dev/null; then
    print_skip "OpenSearch (already running on :9200)"
    OPENSEARCH_OK=true
else
    print_info "Starting OpenSearch via Docker..."
    if docker ps -a --format '{{.Names}}' | grep -q '^zarailink-opensearch$'; then
        docker start zarailink-opensearch
    else
        docker run -d \
            --name zarailink-opensearch \
            -p 9200:9200 -p 9600:9600 \
            -e "discovery.type=single-node" \
            -e "DISABLE_SECURITY_PLUGIN=true" \
            -e "OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m" \
            opensearchproject/opensearch:2.11.0
    fi

    print_info "Waiting for OpenSearch to be ready (up to 60 seconds)..."
    for i in $(seq 1 12); do
        sleep 5
        if curl -s --connect-timeout 3 "http://localhost:9200" | grep -q '"tagline"'; then
            OPENSEARCH_OK=true
            break
        fi
        echo -n "."
    done
    echo ""

    if $OPENSEARCH_OK; then
        print_step "OpenSearch is running"
    else
        print_warn "OpenSearch did not start in time. Search may not work."
        print_warn "Check: docker logs zarailink-opensearch"
    fi
fi

# Index trade data into OpenSearch (if trade data exists and OS is up)
if $OPENSEARCH_OK && [ "$TX_COUNT" -gt 0 ] 2>/dev/null; then
    print_info "Indexing trade data into OpenSearch (this may take a few minutes)..."
    python manage.py index_opensearch --full \
        && print_step "OpenSearch index populated" \
        || print_warn "OpenSearch indexing failed — search will fall back to ORM"
elif $OPENSEARCH_OK; then
    print_info "No trade data to index yet. Import data first, then run:"
    print_info "  python manage.py index_opensearch --full"
fi

# =============================================================================
# SEMANTIC SEARCH INDEX (FAISS / SentenceTransformer)
# =============================================================================
print_header "SEMANTIC SEARCH INDEX"

if [ -f "search_index.pkl" ]; then
    print_skip "Semantic search index (search_index.pkl)"
else
    print_info "Building semantic search index (downloads ~90 MB model on first run)..."
    python manage.py build_search_index \
        && print_step "Semantic search index built" \
        || { print_error "Failed to build search index!"; print_error "Run manually: python manage.py build_search_index"; }
fi

# =============================================================================
# DOCKER SERVICES (Redis cache)
# =============================================================================
print_header "REDIS CACHE"

if docker ps --format '{{.Names}}' | grep -q '^zarailink-redis$'; then
    print_skip "Redis container"
else
    print_info "Starting Redis..."
    if docker ps -a --format '{{.Names}}' | grep -q '^zarailink-redis$'; then
        docker start zarailink-redis
    else
        docker run -d --name zarailink-redis -p 6379:6379 redis:7-alpine
    fi
    print_step "Redis started"
fi

# =============================================================================
# FRONTEND SETUP
# =============================================================================
print_header "FRONTEND SETUP"

cd "$SCRIPT_DIR/frontend"

# Always run npm install — it's a no-op if nothing changed
print_info "Installing/updating frontend dependencies..."
npm install --legacy-peer-deps --silent
print_step "Frontend dependencies ready (jsPDF, Recharts, etc.)"

# =============================================================================
# FINAL OUTPUT
# =============================================================================
cd "$SCRIPT_DIR"

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║${NC}                                                                  ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  ${BOLD}${GREEN}✓  SETUP COMPLETE!${NC}                                            ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}                                                                  ${GREEN}║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║${NC}                                                                  ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  ${BOLD}TO START THE APPLICATION:${NC}                                     ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}                                                                  ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  ${CYAN}Terminal 1 — Backend:${NC}                                          ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}    cd backend                                                   ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}    source .venv/bin/activate                                    ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}    python manage.py runserver                                   ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}                                                                  ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  ${CYAN}Terminal 2 — Frontend:${NC}                                         ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}    cd frontend && npm start                                     ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}                                                                  ${GREEN}║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║${NC}                                                                  ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  ${BOLD}ACCESS:${NC}                                                        ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}    App:          ${CYAN}http://localhost:3000${NC}                          ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}    Django Admin: ${CYAN}http://localhost:8000/admin${NC}                    ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}    OpenSearch:   ${CYAN}http://localhost:9200${NC}                          ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}                                                                  ${GREEN}║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║${NC}                                                                  ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  ${YELLOW}⚠  OPTIONAL — configure in backend/.env:${NC}                      ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}    OPENAI_KEY          — AI search suggestions                  ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}    EMAIL_HOST_USER/PASSWORD — email verification                ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}                                                                  ${GREEN}║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""
