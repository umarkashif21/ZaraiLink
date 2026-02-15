# =============================================================================
# ZaraiLink Setup Script for Windows (PowerShell)
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
#   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
#   .\setup_windows.ps1
# =============================================================================

$ErrorActionPreference = "Stop"

# Colors for output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Print-Header($message) {
    Write-Host ""
    Write-Host "==================================================================" -ForegroundColor Blue
    Write-Host "  $message" -ForegroundColor Cyan
    Write-Host "==================================================================" -ForegroundColor Blue
}

function Print-Step($message) {
    Write-Host "[OK] " -ForegroundColor Green -NoNewline
    Write-Host $message
}

function Print-Skip($message) {
    Write-Host "[--] " -ForegroundColor Yellow -NoNewline
    Write-Host "$message (already exists, skipping)" -ForegroundColor Yellow
}

function Print-Info($message) {
    Write-Host "[i] " -ForegroundColor Cyan -NoNewline
    Write-Host $message
}

function Print-Error($message) {
    Write-Host "[X] " -ForegroundColor Red -NoNewline
    Write-Host $message -ForegroundColor Red
}

function Test-Command($command) {
    return [bool](Get-Command -Name $command -ErrorAction SilentlyContinue)
}

# =============================================================================
# PRE-FLIGHT CHECKS
# =============================================================================
Print-Header "PRE-FLIGHT CHECKS"

# Check Python
if (-not (Test-Command "python")) {
    Print-Error "Python is not installed. Please install Python 3.12+ from python.org"
    exit 1
}
$pythonVersion = python --version 2>&1
Print-Step "Python found: $pythonVersion"

# Check Node.js
if (-not (Test-Command "node")) {
    Print-Error "Node.js is not installed. Please install from nodejs.org"
    exit 1
}
$nodeVersion = node --version
Print-Step "Node.js found: $nodeVersion"

# Check npm
if (-not (Test-Command "npm")) {
    Print-Error "npm is not installed. It should come with Node.js"
    exit 1
}
$npmVersion = npm --version
Print-Step "npm found: $npmVersion"

# Check Docker
if (-not (Test-Command "docker")) {
    Print-Error "Docker is not installed. Please install Docker Desktop."
    exit 1
}
$dockerInfo = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Print-Error "Docker is not running. Please start Docker Desktop."
    exit 1
}
Print-Step "Docker is running"

# Check PostgreSQL
if (-not (Test-Command "psql")) {
    Print-Error "PostgreSQL psql is not in PATH. Please add PostgreSQL bin folder to PATH."
    Print-Error "  Typically: C:\Program Files\PostgreSQL\15\bin"
    exit 1
}
Print-Step "PostgreSQL found"

# Get script directory (project root)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir
Print-Step "Working directory: $ScriptDir"

# =============================================================================
# BACKEND SETUP
# =============================================================================
Print-Header "BACKEND SETUP"

Set-Location "$ScriptDir\backend"

# Virtual environment
if (-not (Test-Path ".venv")) {
    Print-Info "Creating virtual environment..."
    python -m venv .venv
    Print-Step "Virtual environment created"
} else {
    Print-Skip "Virtual environment"
}

# Activate virtual environment
& ".\.venv\Scripts\Activate.ps1"
Print-Step "Virtual environment activated"

# ALWAYS install/upgrade dependencies to ensure all packages are present
Print-Info "Installing Python dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# Verify critical packages installed
$criticalPackages = @("django", "numpy", "pandas", "openpyxl", "sentence-transformers", "lightgbm")
foreach ($pkg in $criticalPackages) {
    $result = pip show $pkg 2>$null
    if ($LASTEXITCODE -ne 0) {
        Print-Error "Failed to install $pkg!"
        exit 1
    }
}
Print-Step "Python dependencies installed and verified"

# Environment file
if (-not (Test-Path ".env")) {
    Print-Info "Creating .env file..."
    Copy-Item ".env.example" ".env"
    
    # Generate SECRET_KEY
    $secretKey = python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
    
    # Update SECRET_KEY in .env
    $envContent = Get-Content ".env" -Raw
    $envContent = $envContent -replace "SECRET_KEY=.*", "SECRET_KEY=$secretKey"
    Set-Content ".env" $envContent -NoNewline
    
    Print-Step ".env file created with generated SECRET_KEY"
} else {
    Print-Skip ".env file"
}

# =============================================================================
# DATABASE SETUP
# =============================================================================
Print-Header "DATABASE SETUP"

# Check if database exists
$dbExists = $false
try {
    $result = psql -U postgres -lqt 2>&1
    if ($result -match "zarailink") {
        $dbExists = $true
    }
} catch {
    # Database check failed, will try to create
}

if ($dbExists) {
    Print-Skip "Database 'zarailink'"
} else {
    Print-Info "Creating PostgreSQL database..."
    Print-Info "(You may be prompted for the postgres password - default: postgres)"
    
    try {
        $env:PGPASSWORD = "postgres"
        createdb -U postgres zarailink
        Print-Step "Database 'zarailink' created"
    } catch {
        Print-Error "Failed to create database. Please create it manually:"
        Print-Error "  createdb -U postgres zarailink"
        exit 1
    } finally {
        Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
    }
}

# Run migrations
Print-Info "Running database migrations..."
python manage.py migrate --no-input
Print-Step "Migrations complete"

# Load database fixture (if available and DB is empty)
$txCount = python manage.py shell -c "from trade_data.models import Transaction; print(Transaction.objects.count())" 2>$null
if ([int]$txCount -gt 0) {
    Print-Skip "Database fixture (data already present)"
} else {
    if (Test-Path "..\load_data.json") {
        Print-Info "Loading database fixture (load_data.json)..."
        try {
            python manage.py loaddata ..\load_data.json
            Print-Step "Database fixture loaded"
        } catch {
            Print-Info "Fixture loading failed, will load data individually below"
        }
    } else {
        Print-Info "No load_data.json found, will load data individually below"
    }
}

# Setup company roles
Print-Info "Setting up company roles..."
python manage.py setup_company_roles
Print-Step "Company roles configured"

# Load sample data for company comparison (if not already loaded)
$companyCount = python manage.py shell -c "from companies.models import Company; print(Company.objects.count())" 2>$null
if ([int]$companyCount -gt 0) {
    Print-Skip "Sample company data"
} else {
    if (Test-Path "load_data.py") {
        Print-Info "Loading sample company data..."
        python load_data.py
        Print-Step "Sample company data loaded"
    } else {
        Print-Info "No load_data.py found, skipping sample data"
    }
}

# Import trade data (needed for GNN embeddings and Similar Companies)
$transactionCount = python manage.py shell -c "from trade_data.models import Transaction; print(Transaction.objects.count())" 2>$null
if ([int]$transactionCount -gt 0) {
    Print-Skip "Trade transaction data"
} else {
    if (Test-Path "..\import_data_1year.xlsx") {
        Print-Info "Importing trade data (this may take a few minutes)..."
        try {
            python manage.py ingest_trade --file ..\import_data_1year.xlsx
            Print-Step "Trade data imported"
        } catch {
            Print-Info "Trade data import skipped (optional)"
        }
    } else {
        Print-Info "No import_data_1year.xlsx found, skipping trade data import"
    }
}

# Build GNN graphs from trade data (needed for Similar Companies)
$transactionCount = python manage.py shell -c "from trade_data.models import Transaction; print(Transaction.objects.count())" 2>$null
if ([int]$transactionCount -gt 0) {
    if (-not (Test-Path "company_product_graph.graphml")) {
        Print-Info "Building GNN graphs from trade data..."
        try {
            python manage.py build_gnn_graphs
            Print-Step "GNN graphs built"
        } catch {
            Print-Info "Graph building skipped (optional feature)"
        }
    } else {
        Print-Skip "GNN graphs"
    }
} else {
    Print-Info "No trade data found, skipping graph building"
}

# Generate GNN embeddings for Similar Companies feature (if not already generated)
$embeddingCount = python manage.py shell -c "from trade_data.models import CompanyEmbedding; print(CompanyEmbedding.objects.count())" 2>$null
if ([int]$embeddingCount -gt 0) {
    Print-Skip "GNN embeddings"
} else {
    if (Test-Path "company_product_graph.graphml") {
        Print-Info "Generating GNN embeddings (this may take several minutes)..."
        try {
            python manage.py generate_gnn_embeddings --fast
            Print-Step "GNN embeddings generated"
        } catch {
            Print-Info "GNN embedding generation skipped (optional feature)"
        }
    } else {
        Print-Info "No graph files found, skipping GNN embeddings"
    }
}

# =============================================================================
# SEARCH ENGINE SETUP
# =============================================================================
Print-Header "SEARCH ENGINE SETUP"

# Build NLP search index (sentence-transformers embeddings for product matching)
if (Test-Path "search_index.pkl") {
    Print-Skip "NLP search index (search_index.pkl)"
} else {
    if ([int]$transactionCount -gt 0) {
        Print-Info "Building NLP search index (downloading model on first run)..."
        try {
            python manage.py build_search_index
            Print-Step "NLP search index built"
        } catch {
            Print-Info "Search index build skipped (optional)"
        }
    } else {
        Print-Info "No trade data found, skipping search index build"
    }
}

# Train LTR (Learning-to-Rank) model
$ltrModelPath = "search\models\lgbm_ltr.txt"
$needsTraining = $false

if (Test-Path $ltrModelPath) {
    $modelSize = (Get-Item $ltrModelPath).Length
    if ($modelSize -gt 1000) {
        Print-Skip "LTR ranking model"
    } else {
        Print-Info "LTR model exists but appears untrained, retraining..."
        $needsTraining = $true
    }
} else {
    if ([int]$transactionCount -gt 0) {
        $needsTraining = $true
    } else {
        Print-Info "No trade data found, skipping LTR model training"
    }
}

if ($needsTraining) {
    Print-Info "Training LTR ranking model..."
    try {
        python -c @"
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()
from search.services.train_ltr import LTRTrainer
LTRTrainer().train()
"@
        Print-Step "LTR ranking model trained"
    } catch {
        Print-Info "LTR training skipped (search will use heuristic ranking)"
    }
}

# =============================================================================
# DOCKER SERVICES (REDIS)
# =============================================================================
Print-Header "DOCKER SERVICES"

# Check if Redis container is running
$redisRunning = docker ps --format '{{.Names}}' 2>&1 | Select-String -Pattern "zarailink-redis"
if ($redisRunning) {
    Print-Skip "Redis container"
} else {
    Print-Info "Starting Redis container..."
    docker-compose up -d
    Print-Step "Redis container started"
}

# =============================================================================
# FRONTEND SETUP
# =============================================================================
Print-Header "FRONTEND SETUP"

Set-Location "$ScriptDir\frontend"

# Install npm dependencies
if (-not (Test-Path "node_modules")) {
    Print-Info "Installing npm dependencies..."
    npm install --legacy-peer-deps --silent
    Print-Step "npm dependencies installed"
} else {
    Print-Skip "node_modules"
}

# =============================================================================
# PUPPETEER SETUP (PDF Generation)
# =============================================================================
Print-Header "PDF GENERATION SETUP"

Set-Location "$ScriptDir\backend"

if (-not (Test-Path "node_modules")) {
    Print-Info "Installing Puppeteer for PDF generation..."
    npm install --silent
    Print-Step "Puppeteer installed"
} else {
    Print-Skip "Puppeteer (node_modules)"
}

# =============================================================================
# FINAL OUTPUT
# =============================================================================
Set-Location $ScriptDir

Write-Host ""
Write-Host "==================================================================" -ForegroundColor Green
Write-Host "|                                                                |" -ForegroundColor Green
Write-Host "|  " -ForegroundColor Green -NoNewline
Write-Host "SETUP COMPLETE!" -ForegroundColor White -NoNewline
Write-Host "                                             |" -ForegroundColor Green
Write-Host "|                                                                |" -ForegroundColor Green
Write-Host "==================================================================" -ForegroundColor Green
Write-Host "|                                                                |" -ForegroundColor Green
Write-Host "|  " -ForegroundColor Green -NoNewline
Write-Host "TO RUN THE APPLICATION:" -ForegroundColor White -NoNewline
Write-Host "                                       |" -ForegroundColor Green
Write-Host "|                                                                |" -ForegroundColor Green
Write-Host "|  " -ForegroundColor Green -NoNewline
Write-Host "Backend:" -ForegroundColor Cyan -NoNewline
Write-Host "                                                       |" -ForegroundColor Green
Write-Host "|    cd backend                                                  |" -ForegroundColor Green
Write-Host "|    .\.venv\Scripts\Activate.ps1                                |" -ForegroundColor Green
Write-Host "|    python manage.py runserver                                  |" -ForegroundColor Green
Write-Host "|                                                                |" -ForegroundColor Green
Write-Host "|  " -ForegroundColor Green -NoNewline
Write-Host "Frontend:" -ForegroundColor Cyan -NoNewline
Write-Host " (in a new PowerShell window)                         |" -ForegroundColor Green
Write-Host "|    cd frontend                                                 |" -ForegroundColor Green
Write-Host "|    npm start                                                   |" -ForegroundColor Green
Write-Host "|                                                                |" -ForegroundColor Green
Write-Host "==================================================================" -ForegroundColor Green
Write-Host "|                                                                |" -ForegroundColor Green
Write-Host "|  " -ForegroundColor Green -NoNewline
Write-Host "ACCESS URLS:" -ForegroundColor White -NoNewline
Write-Host "                                                   |" -ForegroundColor Green
Write-Host "|    Frontend:     " -ForegroundColor Green -NoNewline
Write-Host "http://localhost:3000" -ForegroundColor Cyan -NoNewline
Write-Host "                          |" -ForegroundColor Green
Write-Host "|    Django Admin: " -ForegroundColor Green -NoNewline
Write-Host "http://localhost:8000/admin" -ForegroundColor Cyan -NoNewline
Write-Host "                    |" -ForegroundColor Green
Write-Host "|    Redis UI:     " -ForegroundColor Green -NoNewline
Write-Host "http://localhost:8001" -ForegroundColor Cyan -NoNewline
Write-Host "                          |" -ForegroundColor Green
Write-Host "|                                                                |" -ForegroundColor Green
Write-Host "==================================================================" -ForegroundColor Green
Write-Host "|                                                                |" -ForegroundColor Green
Write-Host "|  " -ForegroundColor Green -NoNewline
Write-Host "OPTIONAL: Configure these in backend\.env:" -ForegroundColor Yellow -NoNewline
Write-Host "                   |" -ForegroundColor Green
Write-Host "|    - OPENAI_KEY (for AI features)                              |" -ForegroundColor Green
Write-Host "|    - EMAIL_HOST_USER/PASSWORD (for email verification)         |" -ForegroundColor Green
Write-Host "|                                                                |" -ForegroundColor Green
Write-Host "==================================================================" -ForegroundColor Green
Write-Host ""
