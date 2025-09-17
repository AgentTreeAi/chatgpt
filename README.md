# Remote-Team Mental-Health Tracker (RMHT)

RMHT is a privacy-first micro-SaaS that helps distributed teams spot burnout and celebrate wins without collecting PII. It combines anonymous weekly check-ins, org-scoped dashboards, Slack nudges, and Stripe billing into a Railway-ready service.

## Architecture

- **API:** FastAPI + Jinja templates (Python 3.11)
- **Database:** Neon Postgres via SQLAlchemy 2.x ORM + Alembic migrations
- **Auth:** Passwordless magic links powered by SendGrid and signed JWT nonces
- **RBAC:** Roles (`org_admin`, `team_lead`, `employee`) enforced per-request with org isolation
- **Integrations:** Slack OAuth install + bot messaging, Stripe subscriptions, Railway cron jobs
- **Privacy:** Request ID middleware, JSON logs, cohort threshold (≥5), retention worker, EWMA-based risk scoring

## Prerequisites

- Python 3.11
- Postgres database (local Docker or Neon)
- SendGrid, Slack, and Stripe sandbox credentials for full feature set

## Quick start (local dev)

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# copy and edit environment
cp .env.example .env
# update secrets as needed. DATABASE_URL is optional in dev and defaults to SQLite.

# run migrations
alembic upgrade head

# launch API
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/` for the marketing home, `/admin` for the org console (use the demo magic-link flow), and `/dashboard/1` for seeded analytics once the Postgres seed runs on startup.

### Database migration commands

```bash
# autogenerate after editing models
alembic revision --autogenerate -m "describe change"
# apply latest
alembic upgrade head
```

### Import existing SQLite demo data

If you previously used the SQLite prototype, migrate the data once:

```bash
python scripts/import_sqlite.py
```

## Environment variables

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | Postgres connection string (`postgresql+psycopg2://...`). Optional when `APP_ENV=dev` (uses SQLite fallback). |
| `SECRET_KEY` | HMAC secret for JWT magic links and sessions |
| `RMHT_ADMIN_TOKEN` | Legacy token for scripting (admins now use magic links) |
| `SENDGRID_API_KEY` | SendGrid API key for passwordless emails |
| `SLACK_CLIENT_ID` / `SLACK_CLIENT_SECRET` | Slack OAuth credentials |
| `STRIPE_SECRET_KEY` | Stripe API key (test mode) |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signature secret |
| `STRIPE_PRICE_*` | Price IDs for Starter/Pro/Enterprise plans |
| `APP_BASE_URL` | Public base URL used in links and Slack prompts |
| `CRON_SECRET` | Shared secret for Railway cron job endpoints |
| `SQLITE_DATABASE_PATH` | Override path for the dev SQLite fallback (defaults to `rmht.db`) |

## Key routes

| Route | Description |
| --- | --- |
| `/` | Marketing home and quick links |
| `/checkin/{token}` | Anonymous employee form (seed token: `demo-token`) |
| `/dashboard/{team_id}` | Aggregated analytics (requires ≥5 check-ins) |
| `/auth/request-link` | Request magic link (POST `{ "email": "admin@example.com" }`) |
| `/admin` | Org admin console (requires magic link session) |
| `/integrations/slack/*` | Install + manage Slack bot |
| `/billing/*` | Stripe checkout, portal, webhooks |
| `/jobs/*` | Railway cron endpoints (weekly Slack prompts, retention, seat sync) |
| `/healthz` | Lightweight uptime probe |

## Observability & privacy

- JSON-formatted logs with per-request IDs
- CSRF-protected admin APIs via session token + header
- Risk engine stores daily EWMA snapshots; raw check-ins purge per retention policy
- Dashboard hides metrics until cohort threshold (5) satisfied

## Testing

```bash
ruff check .
mypy app  # optional
pytest
```

GitHub Actions (`.github/workflows/`) run lint, type-check, pytest, build, and Railway deployment (when secrets exist).

## Deployment

The provided Dockerfile builds a slim Uvicorn image running as a non-root user. Build & push via `docker buildx` or let GitHub Actions publish to GHCR. Deployments trigger `railway up --ci` when `RAILWAY_TOKEN` is configured.

## Roadmap

- Microsoft Teams + calendar insights (currently stubs)
- Stripe metered billing refinements for enterprise plans
- Automated SOC2-ready logging and audit exports

## License

MIT
