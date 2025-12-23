# AuditMind

AuditMind is an AI-assisted evidence classification system for security and compliance teams. It ingests evidence (text or JSON), maps it to SOC 2 controls, tracks pipeline runs, and surfaces remediation tasks. This repo contains:

- `auditmind_server/` + `audit_api/`: Django REST API, orchestration engine, and classifiers.
- `frontend/`: Angular 19 dashboard for uploading evidence and reviewing results.
- `var/`: runtime storage for uploads, agent logs, and sample payloads (`var/samples/`).

Legacy FastAPI artifacts under `app/` are kept for reference; Django is the active stack.

## Prerequisites

- Python 3.11+
- PostgreSQL 14+ (default database/user/password: `auditmind` / `auditmind` / `auditmind`, host `localhost`, port `5432`)
- Redis (for async/background jobs via `django_rq`; sync mode works without it)
- Node.js 18+ and npm (for the Angular dashboard)
- `pip` + `venv` (bundled with Python)

Optional: `pgcli` for DB inspection, `ruff` for linting.

## Quick Start (Backend)

```bash
git clone <repo-url> auditmind-backend
cd auditmind-backend

python3 -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate

pip install --upgrade pip
pip install -r requirements.txt
```

Configure DB settings if you are not using the defaults:

```bash
export DB_NAME=<name>
export DB_USER=<user>
export DB_PASSWORD=<password>
export DB_HOST=<host>
export DB_PORT=<port>
```

Create the database/user in Postgres, then apply migrations and seed SOC 2 controls:

```bash
python manage.py migrate
python manage.py seed_soc2_controls
python manage.py createsuperuser   # optional admin UI login
```

Run the API:

```bash
python manage.py runserver 0.0.0.0:8000
```

- API base path: `/api/`
- Health check: `GET /api/health/`
- Media/uploads live under `var/uploads/` (created automatically).

### Background jobs (optional)

Async classification uses Redis + RQ:

```bash
# in another terminal
redis-server          # or your managed Redis
python manage.py rqworker default
```

Then call `POST /api/evidence/<id>/classify/?async=1` to enqueue.

## Frontend (Angular dashboard)

```bash
cd frontend
npm install
npm start             # http://localhost:4200 proxied to http://localhost:8000/api
```

The dashboard lets you register/login, pick an organization, upload evidence, trigger classification, and review pipeline steps, control matches, and tasks.

## API Flow

Auth uses DRF token authentication.

1) `POST /api/auth/register/` → creates user, organization, and admin membership.  
2) `POST /api/auth/login/` → returns token; include `Authorization: Token <token>` on subsequent calls.  
3) `POST /api/organizations/` (admins) → additional orgs.  
4) `POST /api/evidence/` with `raw_text` or `raw_json` (or `POST /api/evidence/upload/` with `file`). Creation auto-runs classification in sync mode.  
5) `POST /api/evidence/<evidence_id>/classify/` (sync) or `...?async=1` (queue).  
6) Fetch evidence/agent run details via `/api/evidence/`, `/api/evidence/<id>/agent-runs/`, `/api/evidence/<id>/timeline/`, `/api/agent-runs/<id>/steps/`, and remediation tasks via `/api/tasks/`.

## Project Structure

- `auditmind_server/settings.py`: Django settings, DB/env knobs, RQ config.
- `audit_api/`: models, services, orchestration engine, API views/urls, background tasks.
- `audit_api/management/commands/seed_soc2_controls.py`: seeds SOC 2 controls.
- `frontend/`: Angular 19 UI (Tailwind enabled) with proxy at `frontend/proxy.conf.json`.
- `var/samples/`: example evidence payloads for manual testing.

## Development Tips

```bash
# Run tests
python manage.py test

# Lint/format (if ruff installed)
ruff check .
ruff format .
```

Deactivate the virtualenv when finished: `deactivate`.

You now have AuditMind running locally with seeded SOC 2 controls and both API + dashboard available for evidence classification.
