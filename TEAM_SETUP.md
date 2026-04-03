# ZaraiLink — Team Setup Guide (Latest Branch)

> **Branch:** `umar_newbranch`  
> **Last Updated:** April 2026  
> This is the definitive guide to get the latest version of ZaraiLink running on your machine from scratch.

---

## ⚡ Quick Answer: What You Need to Do

1. Clone the repo & switch to the correct branch
2. Set up PostgreSQL + create the database
3. Set up Python virtual environment + install deps
4. Configure `.env`
5. Run migrations + load data
6. Start Redis via Docker
7. Set up & run frontend

Total time: **~20–30 minutes** on a fresh machine.

---

## 📋 Prerequisites

Install these before starting:

| Tool | Version | Download |
|------|---------|----------|
| Python | 3.12+ | [python.org](https://www.python.org/downloads/) |
| Node.js | 18+ LTS | [nodejs.org](https://nodejs.org/) |
| PostgreSQL | 15+ | [postgresql.org](https://www.postgresql.org/download/) |
| Docker Desktop | Latest | [docker.com](https://www.docker.com/products/docker-desktop/) |
| Git | Any | [git-scm.com](https://git-scm.com/) |

Verify everything is installed:
```bash
python --version
node --version
npm --version
docker --version
psql --version
```

---

## Step 1 — Clone the Repo

```bash
git clone https://github.com/umarkashif21/ZaraiLink.git
cd ZaraiLink
git checkout umar_newbranch
git pull origin umar_newbranch
```

> ⚠️ **Important:** Always work on `umar_newbranch` — that's where all the latest changes are.

---

## Step 2 — PostgreSQL Database Setup

The app uses PostgreSQL with these hardcoded defaults in `settings.py`:

| Setting | Value |
|---------|-------|
| Database | `zarailink` |
| Username | `postgres` |
| Password | `postgres` |
| Host | `localhost` |
| Port | `5432` |

### Create the database:

**Windows:**
```powershell
# Make sure PostgreSQL bin is in PATH first
# e.g. C:\Program Files\PostgreSQL\15\bin
createdb -U postgres zarailink
# Enter password: postgres
```

**Mac:**
```bash
createdb zarailink
```

**Linux:**
```bash
sudo -u postgres createdb zarailink
```

**Alternative (any OS) — use psql directly:**
```sql
psql -U postgres
CREATE DATABASE zarailink;
\q
```

---

## Step 3 — Backend Setup

### 3.1 Create & Activate Virtual Environment

**Windows (PowerShell):**
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
> If you get an execution policy error, first run:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

**Mac / Linux:**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
```

### 3.2 Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> This installs Django, DRF, ML libraries (sentence-transformers, scikit-learn, etc.), and all other dependencies. It may take a few minutes.

---

## Step 4 — Configure Environment Variables

```bash
# Windows
copy .env.example .env

# Mac / Linux
cp .env.example .env
```

Edit the `.env` file:

```env
# Generate a Django secret key (run this command and paste the output):
# python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY=<paste-generated-key-here>

# Frontend URL (keep as-is for local dev)
FRONTEND_URL=http://localhost:3000

# Email (Optional — email verification won't work without this)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password

# OpenAI API Key (Optional — AI Smart Search disabled without this)
OPENAI_KEY=sk-your-openai-api-key
```

> 📌 **Note on ML Models:** The large model files (`*.safetensors`, `*.pt`) are **NOT in the repo** (they exceed GitHub's size limits). The app will use lightweight fallback logic for search if the models aren't present locally. Ask Umar for the model files if you need full ML functionality, or re-train them using:
> ```bash
> python scripts/train_intent_model.py
> ```

---

## Step 5 — Run Migrations & Seed Data

Make sure your virtual environment is activated and you're in the `backend/` directory.

```bash
# Run all DB migrations
python manage.py migrate

# Set up company roles (required)
python manage.py setup_company_roles

# Create a superuser (optional, for admin panel access)
python manage.py createsuperuser
```

### 5.1 Load Trade Data (Required for search to work)

```bash
# Import trade data (imports)
python manage.py ingest_trade

# Import trade data (exports)
python manage.py ingest_trade_export

# Build the search index
python manage.py build_search_index

# Import company data
python manage.py import_companies

# Index companies for search
python manage.py index_companies

# Generate company embeddings (for Similar Companies feature)
python manage.py generate_embeddings
```

> ⏱️ These commands process large datasets and may take **5–20 minutes** depending on your machine. Run them in order.

### 5.2 Optional — Trade Lens Data

```bash
python manage.py populate_tradelens
```

---

## Step 6 — Start Redis (Required)

Redis is used for caching. Make sure Docker Desktop is running, then:

```bash
# From the backend/ directory
docker-compose up -d
```

This starts Redis Stack on:
- **Redis:** `localhost:6379`
- **Redis Insight UI:** [http://localhost:8001](http://localhost:8001)

---

## Step 7 — Frontend Setup

Open a **new terminal**:

```bash
cd frontend
npm install
# If you get peer dependency errors:
# npm install --legacy-peer-deps
```

---

## Step 8 — Run the App

You need **two terminals running simultaneously**:

### Terminal 1 — Backend
```bash
cd backend
.\.venv\Scripts\Activate.ps1   # Windows
# OR
source .venv/bin/activate       # Mac/Linux

python manage.py runserver
```

### Terminal 2 — Frontend
```bash
cd frontend
npm start
```

### Access Points

| Service | URL |
|---------|-----|
| **Frontend App** | http://localhost:3000 |
| **Backend API** | http://localhost:8000/api/ |
| **Django Admin** | http://localhost:8000/admin |
| **Redis Insight** | http://localhost:8001 |

---

## 🔧 Troubleshooting

### `ModuleNotFoundError: No module named 'django'`
Virtual environment not activated. Run the activate command again.

### `FATAL: database "zarailink" does not exist`
Run the createdb command from Step 2.

### `Redis connection refused`
Docker isn't running or Redis container isn't up. Run `docker-compose up -d` from `backend/`.

### `npm ERR! ERESOLVE unable to resolve dependency tree`
```bash
npm install --legacy-peer-deps
```

### PowerShell execution policy error
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### `psql: command not found`
Add PostgreSQL's `bin` folder to your system PATH.
- **Windows:** `C:\Program Files\PostgreSQL\15\bin`
- **Mac:** `brew install postgresql@15`
- **Linux:** `sudo apt install postgresql postgresql-contrib`

### Search returns no results
The search index hasn't been built yet. Run:
```bash
python manage.py build_search_index
python manage.py sync_search
```

---

## 📁 Project Structure

```
ZaraiLink/
├── backend/                    # Django REST API (Python 3.12)
│   ├── accounts/               # Auth, users, subscriptions
│   ├── companies/              # Company directory & search
│   ├── trade_ledger/           # Trade data & transactions
│   ├── trade_lens/             # Trade analytics
│   ├── market_intel/           # Market intelligence
│   ├── search/                 # ML-powered search engine
│   │   └── models/             # ⚠️ NOT in repo (too large for GitHub)
│   ├── zarailink/              # Django settings & URLs
│   ├── requirements.txt
│   ├── manage.py
│   └── docker-compose.yml      # Redis config
│
├── frontend/                   # React app
│   ├── src/
│   │   ├── components/         # All UI components
│   │   └── App.js
│   └── package.json
│
├── TEAM_SETUP.md               # ← You are here
└── SETUP.md                    # Legacy setup guide
```

---

## 🤝 Notes for the Team

- **ML Models are not in the repo.** The `*.safetensors` and `*.pt` files are gitignored because they exceed GitHub's file size limits. Contact Umar if you need them.
- **Never commit model files.** They're in `.gitignore` — keep it that way.
- **Always work on `umar_newbranch`** unless told otherwise.
- **Don't push `.env`** — it's gitignored but double-check before committing.
