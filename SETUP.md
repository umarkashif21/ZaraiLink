# ZaraiLink - Developer Setup Guide

> **Target Audience:** Developers who have only installed **Python 3.12**, **Node.js/npm**, and **Docker** on their machine.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (Automated)](#quick-start-automated)
3. [Manual Setup Instructions](#manual-setup-instructions)
4. [Environment Variables Reference](#environment-variables-reference)
5. [Gmail App Password Setup](#gmail-app-password-setup)
6. [Running the Application](#running-the-application)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you begin, ensure you have the following installed:

| Software | Required Version | Download Link |
|----------|------------------|---------------|
| **Python** | 3.12+ | [python.org](https://www.python.org/downloads/) |
| **Node.js** | 18+ (LTS) | [nodejs.org](https://nodejs.org/) |
| **npm** | 9+ (comes with Node.js) | Included with Node.js |
| **Docker Desktop** | Latest | [docker.com](https://www.docker.com/products/docker-desktop/) |
| **PostgreSQL** | 15+ | [postgresql.org](https://www.postgresql.org/download/) |

### Verify Installations

```bash
# Check versions (run in terminal)
python --version    # or python3 --version on Mac/Linux
node --version
npm --version
docker --version
psql --version
```

---

## Quick Start (Automated)

We provide automation scripts for each operating system. These scripts handle everything automatically.

### macOS
```bash
chmod +x setup_mac.sh
./setup_mac.sh
```

### Linux (Ubuntu 22/24)
```bash
chmod +x setup_linux.sh
./setup_linux.sh
```

### Windows (PowerShell)
```powershell
# Run PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\setup_windows.ps1
```

> **Note:** The scripts are idempotent—running them multiple times is safe. They skip steps that are already complete.

---

## Manual Setup Instructions

If you prefer manual setup or need to troubleshoot, follow these steps:

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd ZaraiLink
```

### Step 2: Backend Setup

#### 2.1 Create Virtual Environment

**macOS / Linux:**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell):**
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
cd backend
python -m venv .venv
.venv\Scripts\activate.bat
```

#### 2.2 Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 2.3 Configure Environment Variables

```bash
# Copy the example file
cp .env.example .env    # macOS/Linux
copy .env.example .env  # Windows
```

Edit `.env` and set the following:

```env
# Generate a new SECRET_KEY (run this command):
# python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY=<paste-generated-key-here>

# Email Configuration (Optional - see Gmail App Password section below)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Frontend URL
FRONTEND_URL=http://localhost:3000

# OpenAI API Key (Optional - AI features will be disabled without this)
OPENAI_KEY=sk-your-openai-api-key
```

> **📌 Important:** The `OPENAI_KEY` is optional but recommended. Without it, AI Smart Search and Similar Companies features will be disabled. Get your API key at [platform.openai.com](https://platform.openai.com/api-keys).

#### 2.4 Create PostgreSQL Database

**macOS (with Homebrew PostgreSQL):**
```bash
createdb zarailink
```

**Linux (Ubuntu):**
```bash
sudo -u postgres createdb zarailink
```

**Windows (Command Prompt):**
```cmd
# Make sure PostgreSQL bin is in PATH, then:
createdb -U postgres zarailink
# Enter password when prompted (default: postgres)
```

**Alternative using psql:**
```sql
psql -U postgres
CREATE DATABASE zarailink;
\q
```

#### 2.5 Run Database Migrations

```bash
python manage.py migrate
```

#### 2.6 Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

#### 2.7 Setup Company Roles

```bash
python manage.py setup_company_roles
```

### Step 3: Frontend Setup

```bash
cd ../frontend    # Navigate to frontend directory from backend
npm install
```

> If you encounter peer dependency warnings, try:
> ```bash
> npm install --legacy-peer-deps
> ```

### Step 4: Start Docker Services (Redis)

```bash
cd ../backend     # Navigate back to backend
docker-compose up -d
```

This starts Redis Stack (required for caching).

---

## Environment Variables Reference

| Variable | Required | Description | Example Value |
|----------|----------|-------------|---------------|
| `SECRET_KEY` | ✅ Yes | Django secret key for cryptographic signing | `django-insecure-abc123...` |
| `EMAIL_HOST_USER` | ❌ No | Gmail address for sending emails | `myapp@gmail.com` |
| `EMAIL_HOST_PASSWORD` | ❌ No | Gmail App Password (16 characters) | `abcd efgh ijkl mnop` |
| `FRONTEND_URL` | ❌ No | URL for email verification links | `http://localhost:3000` |
| `OPENAI_KEY` | ❌ No | OpenAI API key for AI features | `sk-proj-abc123...` |

### Database Configuration (Hardcoded in settings.py)

The application uses these default PostgreSQL settings:

| Setting | Value |
|---------|-------|
| Database Name | `zarailink` |
| Username | `postgres` |
| Password | `postgres` |
| Host | `localhost` |
| Port | `5432` |

---

## Gmail App Password Setup

To enable email verification features, you need a Gmail App Password:

### Step 1: Enable 2-Step Verification
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Under "How you sign in to Google", click **2-Step Verification**
3. Follow the prompts to enable it

### Step 2: Generate App Password
1. Go to [App Passwords](https://myaccount.google.com/apppasswords)
2. Select app: **Mail**
3. Select device: **Other (Custom name)** → Enter "ZaraiLink"
4. Click **Generate**
5. Copy the 16-character password (looks like: `abcd efgh ijkl mnop`)

### Step 3: Update .env
```env
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=abcdefghijklmnop  # Remove spaces from the password
```

> **⚠️ Security:** Never commit your `.env` file to version control. It's already in `.gitignore`.

---

## Running the Application

### Start Backend Server

```bash
cd backend
source .venv/bin/activate    # macOS/Linux
# OR
.\.venv\Scripts\Activate.ps1 # Windows PowerShell

python manage.py runserver
```

Backend runs at: **http://localhost:8000**

### Start Frontend Server

```bash
cd frontend
npm start
```

Frontend runs at: **http://localhost:3000**

### Start Redis (if not running)

```bash
cd backend
docker-compose up -d
```

### Access Points

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:3000 |
| **Backend API** | http://localhost:8000/api/ |
| **Django Admin** | http://localhost:8000/admin |
| **Redis Insight** | http://localhost:8001 |

---

## Troubleshooting

### Common Issues

#### 1. `ModuleNotFoundError: No module named 'django'`
**Cause:** Virtual environment not activated.  
**Solution:**
```bash
source .venv/bin/activate    # macOS/Linux
.\.venv\Scripts\Activate.ps1 # Windows
```

#### 2. `FATAL: database "zarailink" does not exist`
**Cause:** PostgreSQL database not created.  
**Solution:**
```bash
createdb zarailink           # macOS
sudo -u postgres createdb zarailink  # Linux
createdb -U postgres zarailink       # Windows
```

#### 3. `Error: ENOENT: no such file or directory, open 'package.json'`
**Cause:** Running npm command from wrong directory.  
**Solution:** Ensure you're in the `frontend` directory.

#### 4. Redis connection refused
**Cause:** Redis container not running.  
**Solution:**
```bash
cd backend
docker-compose up -d
```

#### 5. `npm ERR! ERESOLVE unable to resolve dependency tree`
**Cause:** Peer dependency conflicts.  
**Solution:**
```bash
npm install --legacy-peer-deps
```

#### 6. PowerShell script execution disabled
**Cause:** Windows execution policy.  
**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 7. `psql: command not found`
**Cause:** PostgreSQL not in system PATH.  
**Solution:**
- **macOS:** Install via Homebrew: `brew install postgresql@15`
- **Linux:** `sudo apt install postgresql postgresql-contrib`
- **Windows:** Add PostgreSQL bin folder to PATH (e.g., `C:\Program Files\PostgreSQL\15\bin`)

---

## Project Structure Quick Reference

```
ZaraiLink/
├── backend/                 # Django REST API
│   ├── .venv/              # Python virtual environment
│   ├── accounts/           # User authentication
│   ├── companies/          # Company directory
│   ├── trade_ledger/       # Trade intelligence
│   ├── zarailink/          # Django settings
│   ├── requirements.txt    # Python dependencies
│   ├── manage.py           # Django CLI
│   └── docker-compose.yml  # Redis configuration
│
├── frontend/               # React application
│   ├── node_modules/       # npm packages
│   ├── src/                # Source code
│   ├── package.json        # npm dependencies
│   └── public/             # Static assets
│
├── SETUP.md               # This file
├── setup_mac.sh           # macOS automation script
├── setup_linux.sh         # Linux automation script
└── setup_windows.ps1      # Windows automation script
```

---

**Generated:** December 15, 2024  
**Version:** 1.0
