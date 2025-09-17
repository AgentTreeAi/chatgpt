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
# update DATABASE_URL, SECRET_KEY, etc.

# run migrations (optional in dev; SQLite fallback auto-creates tables)
alembic upgrade head

# launch API
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/` for the marketing home, `/admin` for the org console (use the demo magic-link flow), and `/dashboard/1` for seeded analytics once the Postgres seed runs on startup.

> **Note:** When `APP_ENV` is set to `development` (default) and `DATABASE_URL` is unset, the backend automatically falls back to a SQLite database stored at `rmht.db`. Production still requires an explicit `DATABASE_URL`.

## Frontend SPA development

The React single-page app lives in [`frontend/`](frontend/) and is built with Vite + Tailwind. It is served by FastAPI at `/app` in production.

### Local development

```bash
# install dependencies
npm --prefix frontend install

# start the Vite dev server (http://localhost:5173)
npm --prefix frontend run dev
```

The backend enables CORS for `http://localhost:5173` out of the box. If you need to expose a different origin (e.g., Replit preview URL), set `CORS_ALLOW_ORIGINS` to a comma-separated list such as:

```bash
CORS_ALLOW_ORIGINS="http://localhost:5173,https://<your-repl-username>.<your-repl-id>.repl.co"
```

### Build & publish the SPA

```bash
npm --prefix frontend ci
npm --prefix frontend run build
python scripts/prepare_frontend.py
```

The helper script copies the Vite `dist/` output into `app/web/dist`, which FastAPI serves at `/app`. Commit the generated assets when deploying via Replit or any environment that does not run the build step automatically.

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
| `APP_ENV` | `development` (default) or `production` |
| `DATABASE_URL` | Postgres connection string; optional in dev (SQLite fallback) |
| `SECRET_KEY` | HMAC secret for JWT magic links and sessions |
| `RMHT_ADMIN_TOKEN` | Legacy token for scripting (admins now use magic links) |
| `CORS_ALLOW_ORIGINS` | Comma-separated origins allowed for CORS |
| `SENDGRID_API_KEY` | SendGrid API key for passwordless emails |
| `SLACK_CLIENT_ID` / `SLACK_CLIENT_SECRET` | Slack OAuth credentials |
| `STRIPE_SECRET_KEY` | Stripe API key (test mode) |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signature secret |
| `STRIPE_PRICE_*` | Price IDs for Starter/Pro/Enterprise plans |
| `APP_BASE_URL` | Public base URL used in links and Slack prompts |
| `CRON_SECRET` | Shared secret for Railway cron job endpoints |

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
mypy app
pytest
```

GitHub Actions (`.github/workflows/`) run lint, type-check, pytest, build, and Railway deployment (when secrets exist).

## Deployment

The provided Dockerfile builds a slim Uvicorn image running as a non-root user. Build & push via `docker buildx` or let GitHub Actions publish to GHCR. Deployments trigger `railway up --ci` when `RAILWAY_TOKEN` is configured.

## Replit setup

1. **Secrets:** Configure the following in the Replit Secrets panel (values shown are safe dev defaults—replace as needed):
   - `APP_ENV=development`
   - `SECRET_KEY=<generate a random 48+ character string>`
   - `RMHT_ADMIN_TOKEN=<generate a random 24+ character string>`
   - Optional: `DATABASE_URL=sqlite:///./rmht.db`
   - Optional: `CORS_ALLOW_ORIGINS=http://localhost:5173,https://<your-replit-preview-host>`
2. **Build the SPA (locally or in the Replit shell):**
   ```bash
   npm --prefix frontend ci
   npm --prefix frontend run build
   python scripts/prepare_frontend.py
   ```
3. **Run command:** `uvicorn app.main:app --host 0.0.0.0 --port 5000`

The backend now boots without a `DATABASE_URL` in development, preventing crash loops during Replit cold starts, while production still enforces explicit Postgres credentials and strong secrets.

## Roadmap

- Microsoft Teams + calendar insights (currently stubs)
- Stripe metered billing refinements for enterprise plans
- Automated SOC2-ready logging and audit exports

## License

MIT
