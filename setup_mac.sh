#!/bin/bash

# =============================================================================
# ZaraiLink Setup Script for macOS
# =============================================================================
# This script automates the complete setup of the ZaraiLink development environment.
# It is idempotent - safe to run multiple times.
#
# Prerequisites:
#   - Python 3.12+
#   - Node.js 18+ and npm
#   - Docker Desktop
#   - PostgreSQL 15+
#
# Usage:
#   chmod +x setup_mac.sh
#   ./setup_mac.sh
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Functions
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
        exit 1
    fi
}

# =============================================================================
# PRE-FLIGHT CHECKS
# =============================================================================
print_header "PRE-FLIGHT CHECKS"

# Check Python
check_command python3
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
print_step "Python found: $PYTHON_VERSION"

# Check Node.js
check_command node
NODE_VERSION=$(node --version)
print_step "Node.js found: $NODE_VERSION"

# Check npm
check_command npm
NPM_VERSION=$(npm --version)
print_step "npm found: $NPM_VERSION"

# Check Docker
check_command docker
if ! docker info &> /dev/null; then
    print_error "Docker is not running. Please start Docker Desktop."
    exit 1
fi
print_step "Docker is running"

# Check PostgreSQL
if ! command -v psql &> /dev/null; then
    print_error "PostgreSQL is not installed. Install via: brew install postgresql@15"
    exit 1
fi
print_step "PostgreSQL found"

# Get script directory (project root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
print_step "Working directory: $SCRIPT_DIR"

# =============================================================================
# BACKEND SETUP
# =============================================================================
print_header "BACKEND SETUP"

cd backend

# Virtual environment - recreate if broken
if [ -d ".venv" ]; then
    # Check if venv is valid
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
        exit 1
    fi
    print_step "Virtual environment created"
else
    print_skip "Virtual environment"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source .venv/bin/activate

# Verify activation worked by checking VIRTUAL_ENV and pip location
if [[ -z "$VIRTUAL_ENV" ]]; then
    print_error "Failed to activate virtual environment (VIRTUAL_ENV is empty)!"
    print_error "Try deleting .venv and running this script again:"
    print_error "  rm -rf .venv && ./setup_mac.sh"
    exit 1
fi

# Double-check pip is from venv, not system
VENV_PIP=".venv/bin/pip"
if [ ! -f "$VENV_PIP" ]; then
    print_error "Venv pip not found at $VENV_PIP!"
    exit 1
fi
print_step "Virtual environment activated: $VIRTUAL_ENV"

# ALWAYS install/upgrade dependencies to ensure all packages are present
print_info "Installing Python dependencies (this may take a minute)..."
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

# Verify critical packages installed
for pkg in django numpy pandas openpyxl; do
    if ! .venv/bin/pip show $pkg &> /dev/null; then
        print_error "Failed to install $pkg!"
        exit 1
    fi
done
print_step "Python dependencies installed and verified"

# Environment file
if [ ! -f ".env" ]; then
    print_info "Creating .env file..."
    cp .env.example .env
    
    # Generate SECRET_KEY (use 'python' since venv is activated)
    SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
    
    # Update SECRET_KEY in .env (macOS sed syntax)
    sed -i '' "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|g" .env
    
    print_step ".env file created with generated SECRET_KEY"
else
    print_skip ".env file"
fi

# =============================================================================
# DATABASE SETUP
# =============================================================================
print_header "DATABASE SETUP"

# Check if database exists
if psql -U postgres -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw zarailink; then
    print_skip "Database 'zarailink'"
else
    print_info "Creating PostgreSQL database..."
    createdb -U postgres zarailink 2>/dev/null || createdb zarailink 2>/dev/null || {
        print_error "Failed to create database. Please create it manually:"
        print_error "  createdb zarailink"
        exit 1
    }
    print_step "Database 'zarailink' created"
fi

# Run migrations
print_info "Running database migrations..."
python manage.py migrate --no-input
print_step "Migrations complete"

# Setup company roles
print_info "Setting up company roles..."
python manage.py setup_company_roles
print_step "Company roles configured"

# =============================================================================
# DOCKER SERVICES (REDIS)
# =============================================================================
print_header "DOCKER SERVICES"

# Check if Redis container is running
if docker ps --format '{{.Names}}' | grep -q 'zarailink-redis'; then
    print_skip "Redis container"
else
    print_info "Starting Redis container..."
    docker-compose up -d
    print_step "Redis container started"
fi

# =============================================================================
# FRONTEND SETUP
# =============================================================================
print_header "FRONTEND SETUP"

cd ../frontend

# Install npm dependencies
if [ ! -d "node_modules" ]; then
    print_info "Installing npm dependencies..."
    npm install --legacy-peer-deps --silent
    print_step "npm dependencies installed"
else
    print_skip "node_modules"
fi

# =============================================================================
# PUPPETEER SETUP (PDF Generation)
# =============================================================================
print_header "PDF GENERATION SETUP"

cd ../backend

if [ ! -d "node_modules" ]; then
    print_info "Installing Puppeteer for PDF generation..."
    npm install --silent
    print_step "Puppeteer installed"
else
    print_skip "Puppeteer (node_modules)"
fi

# =============================================================================
# FINAL OUTPUT
# =============================================================================
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
echo -e "${GREEN}║${NC}  ${CYAN}Backend:${NC}                                                       ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}    cd backend                                                   ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}    source .venv/bin/activate                                    ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}    python manage.py runserver                                   ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}                                                                  ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  ${CYAN}Frontend:${NC} (in a new terminal)                                  ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}    cd frontend                                                  ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}    npm start                                                    ${GREEN}║${NC}"
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
