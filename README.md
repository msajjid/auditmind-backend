# AuditMind Backend

AuditMind is an AI-assisted evidence classification platform. This repo hosts the Django REST API plus orchestration/agent code that ingests evidence, runs the evidence-classification pipeline, and persists classifier outputs/tasks.

## Stack Overview

- Django 5 + Django REST Framework (`auditmind_server/`, `audit_api/`)
- PostgreSQL (primary datastore and FTS)
- Local file storage under `var/uploads/` for raw evidence blobs
- Agents + services in `audit_api/agents` and `audit_api/services` coordinate classification

Legacy FastAPI code still lives under `app/` for reference, but the Django stack is the canonical implementation.

## Prerequisites

| Dependency | Notes |
| --- | --- |
| Python 3.11+ | Install via python.org or Homebrew (`brew install python@3.11`). Confirm with `python3 --version`. |
| PostgreSQL 14+ | Create a database/user the API can use. Defaults: database `auditmind`, user `auditmind`, password `auditmind`, host `localhost`, port `5432`. |
| pip + venv | Included with Python 3. |

Optional but recommended: `pgcli` for DB inspection, `ruff` for linting.

## Local Setup

```bash
git clone <repo-url> auditmind-backend
cd auditmind-backend

# Create & activate virtual env
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

`requirements.txt` should include Django, djangorestframework, psycopg2-binary, plus any FastAPI-era deps you still need.

### Environment Variables

`auditmind_server/settings.py` reads database settings directly; export custom values if you’re not using the defaults:

```bash
export DB_NAME=<name>
export DB_USER=<user>
export DB_PASSWORD=<password>
export DB_HOST=<host>
export DB_PORT=<port>
```

### Database Migrations

```bash
python manage.py migrate
```

### Seed Reference Data

Populate the SOC 2 framework + controls:

```bash
python manage.py seed_soc2_controls
```

## Running the API

```bash
python manage.py runserver 0.0.0.0:8000
```

Endpoints (all prefixed with `/api/`):

- `GET /api/health/`
- `GET|POST /api/organizations/`
- `GET|POST /api/evidence/?organization_id=<uuid>`
- `POST /api/evidence/<uuid:evidence_id>/classify/`

## Typical Flow

1. `POST /api/organizations/` → capture organization ID.
2. `POST /api/evidence/` with metadata plus `raw_text` or `raw_json`.
3. `POST /api/evidence/<evidence_id>/classify/` to run the classifier.
4. Retrieve evidence again or query `ClassifierOutput` if needed.

Behind the scenes the classifier:

- Stores raw payloads in `var/uploads/<org>/<evidence>/`.
- Normalizes text via `EvidencePreprocessingService`.
- Uses Postgres full-text search (`ControlSearchService`) to rank SOC 2 controls.
- Persists `AiPipelineRun`, `ClassifierOutput`, and optionally creates remediation `Task` rows for top matches.

## Development Tips

```bash
# Run tests
python manage.py test

# Lint/format (if ruff installed)
ruff check .
ruff format .

# Create superuser (optional admin)
python manage.py createsuperuser
```

Deactivate the venv when finished:

```bash
deactivate
```

You now have the AuditMind backend running locally with seeded controls and an operational evidence-classification pipeline.

## Frontend Dashboard (Angular)

An Angular 19 dashboard lives in `frontend/` to manage organizations, upload evidence, and visualize classification pipeline runs.

### Setup

1. Install Node.js 18+.
2. `cd frontend && npm install`
3. Run the dev server with API proxying to Django: `npm start` (http://localhost:4200 → http://localhost:8000).

### Features

- Create/select organizations, with quick reload buttons for org/evidence lists.
- Upload evidence as raw text or JSON; submits to `POST /api/evidence/` and surfaces returned classification output.
- Pipeline monitor showing each evidence item, pipeline stages, cache-hit signals, controls, and confidence.
- Evidence log table with classification badges and control tags.
- Tailwind CSS is enabled via `tailwind.config.js` and `postcss.config.js`; global styles include both Tailwind utilities and custom theme tokens in `src/styles.css`.

### Auth / IAM

- New auth endpoints: `POST /api/auth/register/` (creates user + org + admin membership), `POST /api/auth/login/`, `GET /api/auth/me/`.
- Token auth is enabled (DRF authtoken). Apply migrations after pulling changes: `python manage.py migrate`.
- API endpoints now require authentication; Health check remains open.
- Organization membership is enforced for evidence listing/creation/classification. Organization creation auto-adds the creator as admin.
