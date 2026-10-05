# RunbookOS — SRE & DevOps Operational Automation Platform

A modern, production-grade **Flask + PostgreSQL** application for managing, versioning, executing, and auditing operational runbooks and Site Reliability Engineering (SRE) standard operating procedures.

---

## 🛠️ Strict Technology Stack

### Backend
- **Python**: 3.12+
- **Framework**: Flask
- **ORM / Database**: SQLAlchemy (Flask-SQLAlchemy) + PostgreSQL 18
- **Database Migrations**: Flask-Migrate (Alembic)
- **Security & Forms**: Flask-WTF / CSRF Protection & Werkzeug security
- **Testing**: pytest (29 comprehensive automated tests)
- **API**: Flask REST API (`/api/...`) with Bearer token & session auth

### Frontend
- **HTML5 & CSS3**
- **UI Framework**: Bootstrap 5 + Bootstrap Icons
- **Scripting**: Vanilla JavaScript (no node/react build step required)
- **Templating**: Jinja2 templates (DevOps dark theme)

### AI Engine (Optional)
- **Provider**: Groq API
- **Model**: `llama-3.3-70b-versatile`
- **Condition**: Strictly enabled **only if `GROQ_API_KEY` is configured**; gracefully disabled with user feedback otherwise.
- **Capabilities**:
  - **AI Runbook Drafter**: Automatically synthesize complete structured runbooks from incident/task descriptions.
  - **AI Step Troubleshooter**: In-flight diagnostic assistance during step-by-step executions.

---

## 📋 System Requirements & Pre-requisites

- **Python**: 3.12+
- **PostgreSQL**: PostgreSQL 14+ (tested on PostgreSQL 18.4)
- **Operating System**: Windows / Linux / macOS

---

## 🚀 Quickstart Guide

### 1. Environment Configuration

Clone or navigate to the project directory and verify `.env`:

```bash
# Copy example configuration if needed
copy .env.example .env
```

Ensure your `.env` contains your PostgreSQL connection string:

```ini
FLASK_APP=run.py
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=your-production-secret-key

# PostgreSQL (PRIMARY AND ONLY APPLICATION DATABASE)
DATABASE_URL=postgresql://postgres@localhost:5432/runbookos

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key
JWT_EXPIRATION_HOURS=24

# Optional: Groq AI Integration (leave blank if not using AI)
GROQ_API_KEY=
GROQ_MODEL=llama-3.3-70b-versatile
```

### 2. Virtual Environment & Dependencies

```powershell
# Create Python 3.12 virtual environment
py -3.12 -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install required dependencies
pip install -r requirements.txt
```

### 3. Database Initialization & Seeding

RunbookOS uses PostgreSQL as its primary and only database. Initialize the database schema and load initial demo operators and standard runbooks:

```powershell
# Create tables in PostgreSQL
python run.py init-db

# Seed demo users, procedures, and initial steps
python run.py seed-db
```

Default credentials:
| Role | Email | Password |
|---|---|---|
| **Admin** | `admin@runbookos.dev` | `Admin@123456` |
| **Engineer** | `engineer@runbookos.dev` | `Engineer@123456` |

### 4. Database Migrations (Flask-Migrate)

RunbookOS uses Flask-Migrate (Alembic) for schema versioning:

```powershell
# Check current migration status
flask --app run.py db current

# Apply migrations
flask --app run.py db upgrade
```

### 5. Running the Application

Start the Flask development server:

```powershell
python run.py
```

The web dashboard is now accessible at `http://127.0.0.1:5000`.

---

## 🧪 Automated Testing (pytest)

The test suite covers models, authentication, password hashing, runbook lifecycle, interactive executions, JSONB snapshotting, REST API, CSRF protection, and Groq AI integrations:

```powershell
# Run the complete test suite
python -m pytest -v
```

All 29 tests validate against PostgreSQL without any SQLite or mock DB substitution.

---

## 📡 REST API Reference

The Flask REST API is available under `/api/` and supports both `Authorization: Bearer <token>` and active web sessions.

### Authentication
- `POST /api/auth/register` — Register a new operator (`name`, `email`, `password`, `role`)
- `POST /api/auth/login` — Authenticate and receive a JWT token
- `GET /api/auth/me` — Retrieve current authenticated profile

### Runbooks
- `GET /api/runbooks` — Paginated list of runbooks (supports `?search=` and `?status=`)
- `POST /api/runbooks` — Create a new runbook with procedural steps
- `GET /api/runbooks/<id>` — Get single runbook specification and steps
- `PUT /api/runbooks/<id>` — Update runbook title, description, or steps
- `DELETE /api/runbooks/<id>` — Soft delete (sets status to `inactive`)
- `POST /api/runbooks/<id>/version` — Create a new version increment
- `GET /api/runbooks/<id>/versions` — Retrieve version history lineage

### Executions
- `POST /api/executions/<runbook_id>/start` — Start an interactive execution with step snapshot
- `GET /api/executions/<execution_id>` — Retrieve execution state and step checklist
- `POST /api/executions/<execution_id>/next` — Advance to next step (auto-completes on final step)
- `POST /api/executions/<execution_id>/complete` — Explicitly complete execution

### Metrics & Auditing
- `GET /api/dashboard/stats` — Real-time operational metrics
- `GET /api/audit` — Immutable audit log trail

### AI Engine (Groq + Llama)
- `GET /api/ai/status` — Reports if Groq API key is configured
- `POST /api/ai/generate-runbook` — AI-generated structured runbook
- `POST /api/ai/troubleshoot` — AI diagnostics for a failing step during execution

---

## 🛡️ Architecture & Database Design

```
users (PostgreSQL)
  ├── runbooks (Foreign Key created_by_id)
  │     ├── steps (Foreign Key runbook_id, ordered)
  │     └── executions (Foreign Key runbook_id, steps_snapshot JSONB)
  └── audit_logs (Foreign Key user_id, action, resource_type, timestamp)
```
