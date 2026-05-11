#!/bin/bash
# ZaraiLink Setup Script for Linux (Ubuntu 22/24)

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

print_header() {
    echo ""
    echo -e "${BLUE}══════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${CYAN}  $1${NC}"
    echo -e "${BLUE}══════════════════════════════════════════════════════════════════${NC}"
}

print_step() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_skip() {
    echo -e "${YELLOW}[⊘]${NC} $1 ${YELLOW}(already exists, skipping)${NC}"
}

print_info() {
    echo -e "${CYAN}[i]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1" >&2
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 is not installed. Please install it first."
        echo -e "${YELLOW}  Try: sudo apt install $2${NC}"
        exit 1
    fi
}

print_header "PRE-FLIGHT CHECKS"

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed."
    echo -e "${YELLOW}  Try: sudo apt install python3 python3-venv python3-pip${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
print_step "Python found: $PYTHON_VERSION"

if ! python3 -m venv --help &> /dev/null; then
    print_error "python3-venv is not installed."
    echo -e "${YELLOW}  Try: sudo apt install python3-venv${NC}"
    exit 1
fi
print_step "python3-venv module available"

if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed."
    echo -e "${YELLOW}  Try: curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -${NC}"
    echo -e "${YELLOW}       sudo apt install -y nodejs${NC}"
    exit 1
fi
NODE_VERSION=$(node --version)
print_step "Node.js found: $NODE_VERSION"

check_command npm "npm"
NPM_VERSION=$(npm --version)
print_step "npm found: $NPM_VERSION"

check_command docker "docker.io"
if ! docker info &> /dev/null 2>&1; then
    print_error "Docker is not running or you don't have permission."
    echo -e "${YELLOW}  Try: sudo systemctl start docker${NC}"
    echo -e "${YELLOW}  Or add user to docker group: sudo usermod -aG docker \$USER${NC}"
    exit 1
fi
print_step "Docker is running"

if ! command -v psql &> /dev/null; then
    print_error "PostgreSQL is not installed."
    echo -e "${YELLOW}  Try: sudo apt install postgresql postgresql-contrib${NC}"
    exit 1
fi
print_step "PostgreSQL found"

if ! systemctl is-active --quiet postgresql 2>/dev/null; then
    print_info "Starting PostgreSQL service..."
    sudo systemctl start postgresql
fi
print_step "PostgreSQL service is running"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
print_step "Working directory: $SCRIPT_DIR"

print_header "BACKEND SETUP"

cd backend

if [ -d ".venv" ]; then
    if [ ! -f ".venv/bin/activate" ] || [ ! -f ".venv/bin/pip" ]; then
        print_info "Existing venv appears broken, recreating..."
        rm -rf .venv
    fi
fi

if [ ! -d ".venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        print_error "Failed to create virtual environment!"
        print_error "Try: sudo apt install python3-venv"
        exit 1
    fi
    print_step "Virtual environment created"
else
    print_skip "Virtual environment"
fi

print_info "Activating virtual environment..."
source .venv/bin/activate

if [[ -z "$VIRTUAL_ENV" ]]; then
    print_error "Failed to activate virtual environment (VIRTUAL_ENV is empty)!"
    print_error "Try deleting .venv and running this script again:"
    print_error "  rm -rf .venv && ./setup_linux.sh"
    exit 1
fi

VENV_PIP=".venv/bin/pip"
if [ ! -f "$VENV_PIP" ]; then
    print_error "Venv pip not found at $VENV_PIP!"
    exit 1
fi
print_step "Virtual environment activated: $VIRTUAL_ENV"

print_info "Installing Python dependencies (this may take a minute)..."
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

for pkg in django numpy pandas openpyxl; do
    if ! .venv/bin/pip show $pkg &> /dev/null; then
        print_error "Failed to install $pkg!"
        exit 1
    fi
done
print_step "Python dependencies installed and verified"

if [ ! -f ".env" ]; then
    print_info "Creating .env file..."
    cp .env.example .env

    SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")

    sed -i "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|g" .env

    print_step ".env file created with generated SECRET_KEY"
else
    print_skip ".env file"
fi

print_header "DATABASE SETUP"

if sudo -u postgres psql -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw zarailink; then
    print_skip "Database 'zarailink'"
else
    print_info "Creating PostgreSQL database..."
    sudo -u postgres createdb zarailink 2>/dev/null || {
        print_error "Failed to create database. Please create it manually:"
        print_error "  sudo -u postgres createdb zarailink"
        exit 1
    }
    print_step "Database 'zarailink' created"

    sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';" 2>/dev/null || true
fi

print_info "Running database migrations..."
python manage.py migrate --no-input
print_step "Migrations complete"

print_info "Setting up company roles..."
python manage.py setup_company_roles
print_step "Company roles configured"

if python manage.py shell -c "from companies.models import Company; exit(0 if Company.objects.count() > 0 else 1)" 2>/dev/null; then
    print_skip "Sample company data"
else
    if [ -f "load_data.py" ]; then
        print_info "Loading sample company data..."
        python load_data.py
        print_step "Sample company data loaded"
    else
        print_info "No load_data.py found, skipping sample data"
    fi
fi

if python manage.py shell -c "from trade_data.models import Transaction; exit(0 if Transaction.objects.count() > 0 else 1)" 2>/dev/null; then
    print_skip "Trade transaction data"
else
    if [ -f "../import_data_1year.xlsx" ]; then
        print_info "Importing trade data (this may take a few minutes)..."
        python manage.py ingest_trade --file ../import_data_1year.xlsx || {
            print_info "Trade data import skipped (optional)"
        }
        print_step "Trade data imported"
    else
        print_info "No import_data_1year.xlsx found, skipping trade data import"
    fi
fi

TRANSACTIONS_COUNT=$(python manage.py shell -c "from trade_data.models import Transaction; print(Transaction.objects.count())" 2>/dev/null)
if [ "$TRANSACTIONS_COUNT" -gt 0 ] 2>/dev/null; then
    if [ ! -f "company_product_graph.graphml" ] || [ "../import_data_1year.xlsx" -nt "company_product_graph.graphml" ]; then
        print_info "Building GNN graphs from trade data..."
        python manage.py build_gnn_graphs || {
            print_info "Graph building skipped (optional feature)"
        }
        print_step "GNN graphs built"
    else
        print_skip "GNN graphs"
    fi
else
    print_info "No trade data found, skipping graph building"
fi

if python manage.py shell -c "from trade_data.models import CompanyEmbedding; exit(0 if CompanyEmbedding.objects.count() > 0 else 1)" 2>/dev/null; then
    print_skip "GNN embeddings"
else
    if [ -f "company_product_graph.graphml" ]; then
        print_info "Generating GNN embeddings (this may take several minutes)..."
        python manage.py generate_gnn_embeddings --fast || {
            print_info "GNN embedding generation skipped (optional feature)"
        }
        print_step "GNN embeddings generated"
    else
        print_info "No graph files found, skipping GNN embeddings"
    fi
fi

print_header "DOCKER SERVICES"

if docker ps --format '{{.Names}}' | grep -q 'zarailink-redis'; then
    print_skip "Redis container"
else
    print_info "Starting Redis container..."
    if docker compose version &> /dev/null; then
        docker compose up -d
    elif command -v docker-compose &> /dev/null; then
        docker-compose up -d
    else
        print_error "Neither 'docker compose' nor 'docker-compose' is available!"
        print_error "Please install Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    fi
    print_step "Redis container started"
fi

print_header "FRONTEND SETUP"

cd ../frontend

if [ ! -d "node_modules" ]; then
    print_info "Installing npm dependencies..."
    npm install --legacy-peer-deps --silent
    print_step "npm dependencies installed"
else
    print_skip "node_modules"
fi

print_header "PDF GENERATION SETUP"

cd ../backend

if [ ! -d "node_modules" ]; then
    print_info "Installing Puppeteer for PDF generation..."
    npm install --silent
    print_step "Puppeteer installed"
else
    print_skip "Puppeteer (node_modules)"
fi

cd "$SCRIPT_DIR"

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║${NC}                                                                  ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  ${BOLD}${GREEN}✓ SETUP COMPLETE!${NC}                                             ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}                                                                  ${GREEN}║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║${NC}                                                                  ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  ${BOLD}TO RUN THE APPLICATION:${NC}                                       ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}                                                                  ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  ${CYAN}1. Start Redis (if not running):${NC}                                ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}     cd backend && docker compose up -d                           ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}                                                                  ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  ${CYAN}2. Start Backend:${NC}                                               ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}     cd backend                                                   ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}     source .venv/bin/activate                                    ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}     python manage.py runserver                                   ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}                                                                  ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  ${CYAN}3. Start Frontend:${NC} (in a new terminal)                          ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}     cd frontend                                                  ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}     npm start                                                    ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}                                                                  ${GREEN}║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║${NC}                                                                  ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  ${BOLD}ACCESS URLS:${NC}                                                   ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}    Frontend:     ${CYAN}http://localhost:3000${NC}                          ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}    Django Admin: ${CYAN}http://localhost:8000/admin${NC}                    ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}    Redis UI:     ${CYAN}http://localhost:8001${NC}                          ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}                                                                  ${GREEN}║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║${NC}                                                                  ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  ${YELLOW}⚠ OPTIONAL: Configure these in backend/.env:${NC}                  ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}    - OPENAI_KEY (for AI features)                               ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}    - EMAIL_HOST_USER/PASSWORD (for email verification)          ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}                                                                  ${GREEN}║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""

