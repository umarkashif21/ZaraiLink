# =============================================================================
# ZaraiLink Setup Script for Windows (PowerShell 5.1+)
# =============================================================================
# Automates the complete setup of the ZaraiLink development environment.
# Idempotent — safe to run multiple times.
#
# Prerequisites:
#   - Python 3.12+    https://www.python.org/downloads/
#   - Node.js 18+     https://nodejs.org/
#   - Docker Desktop  https://www.docker.com/products/docker-desktop/
#   - PostgreSQL 15+  https://www.postgresql.org/download/windows/
#     (add C:\Program Files\PostgreSQL\15\bin to PATH)
#
# Usage (run once to allow local scripts):
#   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
#   .\setup_windows.ps1
# =============================================================================

$ErrorActionPreference = "Stop"

# ── Helpers ───────────────────────────────────────────────────────────────────
function Print-Header($msg) {
    Write-Host ""
    Write-Host "==================================================================" -ForegroundColor Blue
    Write-Host "  $msg" -ForegroundColor Cyan
    Write-Host "==================================================================" -ForegroundColor Blue
}
function Print-Step($msg)  { Write-Host "[OK] $msg" -ForegroundColor Green }
function Print-Skip($msg)  { Write-Host "[--] $msg (already done, skipping)" -ForegroundColor Yellow }
function Print-Info($msg)  { Write-Host "[i]  $msg" -ForegroundColor Cyan }
function Print-Warn($msg)  { Write-Host "[!]  $msg" -ForegroundColor Yellow }
function Print-Error($msg) { Write-Host "[X]  $msg" -ForegroundColor Red }

function Test-Cmd($cmd) { return [bool](Get-Command -Name $cmd -ErrorAction SilentlyContinue) }

function Wait-OpenSearch {
    Print-Info "Waiting for OpenSearch to be ready (up to 60 seconds)..."
    for ($i = 1; $i -le 12; $i++) {
        Start-Sleep -Seconds 5
        try {
            $r = Invoke-RestMethod -Uri "http://localhost:9200" -TimeoutSec 3 -ErrorAction Stop
            if ($r.tagline) { return $true }
        } catch {}
        Write-Host "." -NoNewline
    }
    Write-Host ""
    return $false
}

# =============================================================================
# PRE-FLIGHT CHECKS
# =============================================================================
Print-Header "PRE-FLIGHT CHECKS"

# Python 3.12+
if (-not (Test-Cmd "python")) {
    Print-Error "Python is not installed or not in PATH."
    Print-Error "Download: https://www.python.org/downloads/"
    exit 1
}
$pyVer = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>&1
$pyParts = $pyVer -split '\.'
if ([int]$pyParts[0] -lt 3 -or ([int]$pyParts[0] -eq 3 -and [int]$pyParts[1] -lt 12)) {
    Print-Error "Python 3.12+ required. Found: $pyVer"
    Print-Error "Download: https://www.python.org/downloads/"
    exit 1
}
Print-Step "Python $pyVer"

# Node.js 18+
if (-not (Test-Cmd "node")) {
    Print-Error "Node.js is not installed or not in PATH."
    Print-Error "Download: https://nodejs.org/"
    exit 1
}
Print-Step "Node.js $(node --version)"

# npm
if (-not (Test-Cmd "npm")) {
    Print-Error "npm not found (should come with Node.js)."
    exit 1
}
Print-Step "npm $(npm --version)"

# Docker Desktop
if (-not (Test-Cmd "docker")) {
    Print-Error "Docker is not installed."
    Print-Error "Download: https://www.docker.com/products/docker-desktop/"
    exit 1
}
$dockerInfo = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Print-Error "Docker is not running. Please start Docker Desktop."
    exit 1
}
Print-Step "Docker running"

# PostgreSQL (psql in PATH)
if (-not (Test-Cmd "psql")) {
    Print-Error "psql not found in PATH."
    Print-Error "Add PostgreSQL bin dir to PATH, typically:"
    Print-Error "  C:\Program Files\PostgreSQL\15\bin"
    exit 1
}
Print-Step "PostgreSQL found"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir
Print-Step "Working directory: $ScriptDir"

# =============================================================================
# BACKEND SETUP
# =============================================================================
Print-Header "BACKEND SETUP"

Set-Location "$ScriptDir\backend"

# Virtual environment
if (Test-Path ".venv") {
    if (-not (Test-Path ".venv\Scripts\activate") -or -not (Test-Path ".venv\Scripts\pip.exe")) {
        Print-Warn "Existing .venv appears broken — recreating..."
        Remove-Item -Recurse -Force .venv
    }
}
if (-not (Test-Path ".venv")) {
    Print-Info "Creating virtual environment..."
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { Print-Error "Failed to create venv!"; exit 1 }
    Print-Step "Virtual environment created"
} else {
    Print-Skip "Virtual environment"
}

& ".\.venv\Scripts\Activate.ps1"
Print-Step "Virtual environment activated"

# Python dependencies
Print-Info "Installing/updating Python dependencies..."
.venv\Scripts\pip.exe install --upgrade pip -q
.venv\Scripts\pip.exe install -r requirements.txt -q
foreach ($pkg in @("django", "numpy", "pandas", "openpyxl", "sentence_transformers", "lightgbm")) {
    $check = .venv\Scripts\pip.exe show $pkg 2>&1
    if ($LASTEXITCODE -ne 0) { Print-Error "Failed to install $pkg!"; exit 1 }
}
Print-Step "Python dependencies installed"

# .env file
if (-not (Test-Path ".env")) {
    Print-Info "Creating .env from .env.example..."
    if (-not (Test-Path ".env.example")) { Print-Error ".env.example not found!"; exit 1 }
    Copy-Item ".env.example" ".env"
    $secretKey = python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
    $envContent = Get-Content ".env" -Raw
    $envContent = $envContent -replace "SECRET_KEY=.*", "SECRET_KEY=$secretKey"
    Set-Content ".env" $envContent -NoNewline
    Print-Step ".env created with generated SECRET_KEY"
} else {
    Print-Skip ".env file"
}

# =============================================================================
# DATABASE SETUP
# =============================================================================
Print-Header "DATABASE SETUP"

$env:PGPASSWORD = "postgres"
try {
    $dbList = psql -U postgres -lqt 2>&1
    $dbExists = $dbList -match "zarailink"
} catch {
    $dbExists = $false
}

if ($dbExists) {
    Print-Skip "Database 'zarailink'"
} else {
    Print-Info "Creating database 'zarailink'..."
    createdb -U postgres zarailink
    if ($LASTEXITCODE -ne 0) {
        Print-Error "Failed to create database. Run manually: createdb -U postgres zarailink"
        exit 1
    }
    Print-Step "Database 'zarailink' created"
}
Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue

# Migrations
Print-Info "Running database migrations..."
python manage.py migrate --no-input
Print-Step "Migrations complete"

# Company roles
Print-Info "Setting up company roles..."
python manage.py setup_company_roles
Print-Step "Company roles configured"

# Sample company data
$companyCount = python manage.py shell -c "from companies.models import Company; print(Company.objects.count())" 2>$null
if ([int]$companyCount -gt 0) {
    Print-Skip "Sample company data"
} else {
    if (Test-Path "load_data.py") {
        Print-Info "Loading sample company data..."
        python load_data.py
        Print-Step "Sample company data loaded"
    } else {
        Print-Info "No load_data.py — skipping sample data"
    }
}

# Trade data import
$txCount = [int](python manage.py shell -c "from trade_data.models import Transaction; print(Transaction.objects.count())" 2>$null)
if ($txCount -gt 0) {
    Print-Skip "Trade transaction data"
} else {
    $xlsxPath = "$ScriptDir\import_data_1year.xlsx"
    if (Test-Path $xlsxPath) {
        Print-Info "Importing trade data (may take several minutes)..."
        python manage.py ingest_trade --file $xlsxPath
        if ($LASTEXITCODE -eq 0) {
            $txCount = [int](python manage.py shell -c "from trade_data.models import Transaction; print(Transaction.objects.count())" 2>$null)
            Print-Step "Trade data imported ($txCount transactions)"
        } else {
            Print-Warn "Trade data import failed — search will return empty results"
        }
    } else {
        Print-Warn "import_data_1year.xlsx not found at $ScriptDir\"
        Print-Warn "Search returns empty results until trade data is imported."
    }
}

# GNN graphs + embeddings
if ($txCount -gt 0) {
    if (-not (Test-Path "company_product_graph.graphml")) {
        Print-Info "Building GNN trade graphs..."
        python manage.py build_gnn_graphs
        if ($LASTEXITCODE -eq 0) { Print-Step "GNN graphs built" } else { Print-Warn "GNN graph build failed (optional)" }
    } else {
        Print-Skip "GNN graphs"
    }

    $embCount = [int](python manage.py shell -c "from trade_data.models import CompanyEmbedding; print(CompanyEmbedding.objects.count())" 2>$null)
    if ($embCount -gt 0) {
        Print-Skip "GNN embeddings"
    } elseif (Test-Path "company_product_graph.graphml") {
        Print-Info "Generating GNN embeddings..."
        python manage.py generate_gnn_embeddings --fast
        if ($LASTEXITCODE -eq 0) { Print-Step "GNN embeddings generated" } else { Print-Warn "GNN embedding generation failed (optional)" }
    }
}

# =============================================================================
# OPENSEARCH SETUP (required for search)
# =============================================================================
Print-Header "OPENSEARCH SETUP"

$opensearchOk = $false
try {
    $osResp = Invoke-RestMethod -Uri "http://localhost:9200" -TimeoutSec 3 -ErrorAction Stop
    if ($osResp.tagline) {
        Print-Skip "OpenSearch (already running on :9200)"
        $opensearchOk = $true
    }
} catch {
    Print-Info "Starting OpenSearch via Docker..."
    $existing = docker ps -a --format '{{.Names}}' 2>&1 | Select-String "zarailink-opensearch"
    if ($existing) {
        docker start zarailink-opensearch | Out-Null
    } else {
        docker run -d `
            --name zarailink-opensearch `
            -p 9200:9200 -p 9600:9600 `
            -e "discovery.type=single-node" `
            -e "DISABLE_SECURITY_PLUGIN=true" `
            -e "OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m" `
            opensearchproject/opensearch:2.11.0 | Out-Null
    }
    $opensearchOk = Wait-OpenSearch
    if ($opensearchOk) { Print-Step "OpenSearch is running" }
    else { Print-Warn "OpenSearch did not start — check: docker logs zarailink-opensearch" }
}

if ($opensearchOk -and $txCount -gt 0) {
    Print-Info "Indexing trade data into OpenSearch..."
    python manage.py index_opensearch --full
    if ($LASTEXITCODE -eq 0) { Print-Step "OpenSearch index populated" }
    else { Print-Warn "OpenSearch indexing failed — search falls back to ORM" }
} elseif ($opensearchOk) {
    Print-Info "No trade data to index yet. After importing, run:"
    Print-Info "  python manage.py index_opensearch --full"
}

# =============================================================================
# SEMANTIC SEARCH INDEX (FAISS / SentenceTransformer)
# =============================================================================
Print-Header "SEMANTIC SEARCH INDEX"

if (Test-Path "search_index.pkl") {
    Print-Skip "Semantic search index (search_index.pkl)"
} else {
    Print-Info "Building semantic search index (downloads ~90 MB model on first run)..."
    python manage.py build_search_index
    if ($LASTEXITCODE -eq 0) { Print-Step "Semantic search index built" }
    else { Print-Error "Failed to build search index. Run manually: python manage.py build_search_index" }
}

# =============================================================================
# REDIS CACHE
# =============================================================================
Print-Header "REDIS CACHE"

$redisRunning = docker ps --format '{{.Names}}' 2>&1 | Select-String "zarailink-redis"
if ($redisRunning) {
    Print-Skip "Redis container"
} else {
    Print-Info "Starting Redis..."
    $redisExists = docker ps -a --format '{{.Names}}' 2>&1 | Select-String "zarailink-redis"
    if ($redisExists) {
        docker start zarailink-redis | Out-Null
    } else {
        docker run -d --name zarailink-redis -p 6379:6379 redis:7-alpine | Out-Null
    }
    Print-Step "Redis started"
}

# =============================================================================
# FRONTEND SETUP
# =============================================================================
Print-Header "FRONTEND SETUP"

Set-Location "$ScriptDir\frontend"
Print-Info "Installing/updating frontend dependencies..."
npm install --legacy-peer-deps --silent
Print-Step "Frontend dependencies ready"

# =============================================================================
# FINAL OUTPUT
# =============================================================================
Set-Location $ScriptDir

Write-Host ""
Write-Host "==================================================================" -ForegroundColor Green
Write-Host "|                                                                |" -ForegroundColor Green
Write-Host "|  SETUP COMPLETE!                                               |" -ForegroundColor Green
Write-Host "|                                                                |" -ForegroundColor Green
Write-Host "=================================================================="-ForegroundColor Green
Write-Host "|                                                                |" -ForegroundColor Green
Write-Host "|  TO START THE APPLICATION:                                     |" -ForegroundColor Green
Write-Host "|                                                                |" -ForegroundColor Green
Write-Host "|  PowerShell 1 - Backend:                                       |" -ForegroundColor Green
Write-Host "|    cd backend                                                  |" -ForegroundColor Green
Write-Host "|    .\.venv\Scripts\Activate.ps1                                |" -ForegroundColor Green
Write-Host "|    python manage.py runserver                                  |" -ForegroundColor Green
Write-Host "|                                                                |" -ForegroundColor Green
Write-Host "|  PowerShell 2 - Frontend:                                      |" -ForegroundColor Green
Write-Host "|    cd frontend                                                 |" -ForegroundColor Green
Write-Host "|    npm start                                                   |" -ForegroundColor Green
Write-Host "|                                                                |" -ForegroundColor Green
Write-Host "=================================================================="-ForegroundColor Green
Write-Host "|  ACCESS:                                                       |" -ForegroundColor Green
Write-Host "|    App:          http://localhost:3000                         |" -ForegroundColor Green
Write-Host "|    Django Admin: http://localhost:8000/admin                   |" -ForegroundColor Green
Write-Host "|    OpenSearch:   http://localhost:9200                         |" -ForegroundColor Green
Write-Host "=================================================================="-ForegroundColor Green
Write-Host "|  OPTIONAL (backend/.env):                                      |" -ForegroundColor Yellow
Write-Host "|    OPENAI_KEY            - AI search suggestions               |" -ForegroundColor Yellow
Write-Host "|    EMAIL_HOST_USER/PASS  - email verification                  |" -ForegroundColor Yellow
Write-Host "=================================================================="-ForegroundColor Green
Write-Host ""
