# Remote-Team Mental-Health Tracker (RMHT)

Privacy-first micro-SaaS that collects anonymous mood/stress check-ins and shows team-level trends.

## Features
- ✅ FastAPI backend with Jinja templates and SQLite (swap for Postgres in prod)
- ✅ Admin portal protected by `RMHT_ADMIN_TOKEN` to add teams and member tokens
- ✅ Employee check-in form with emoji-inspired scales and optional notes
- ✅ Dashboard with aggregated analytics, risk badge, Chart.js visualizations, and roster insights
- ✅ Integration stubs for Slack, Microsoft Teams, calendars, and HRIS sync

## Tech stack
- FastAPI + SQLAlchemy + SQLite (dev)
- Jinja2 templates styled via Tailwind CSS CDN
- Chart.js for mood/stress trends

## Getting started
```bash
# Install dependencies
pip install fastapi uvicorn[standard] sqlalchemy jinja2 python-multipart

# Run the development server
uvicorn rmht_app.main:app --reload --port 8000
```

Open <http://localhost:8000> to see the marketing home, dashboard demo, and admin link.

## Key routes
- `/` – Home with product overview and demo shortcuts
- `/checkin/{token}` – Anonymous employee check-in (use `demo-alex` for the sample data)
- `/dashboard/{team_id}` – Aggregated charts and qualitative notes per team
- `/admin?token=...` – Token-protected admin portal to create teams and tokens
- `/healthz` – Lightweight health probe

## Configuration
Environment variables:

| Variable | Default | Description |
| --- | --- | --- |
| `RMHT_ADMIN_TOKEN` | `changeme` | Token required for the admin portal |
| `RMHT_DATABASE_URL` | `sqlite:///./rmht.db` | Database connection string |

SQLite data is written to `rmht.db`. Add it to `.gitignore` for production deployments.

## Demo data
On first startup the app seeds a "Remote Success" team with three demo members (`demo-alex`, `demo-brook`, `demo-cam`) and recent check-ins so the dashboard renders immediately.

## Next steps before launch
- Replace SQLite with Postgres
- Swap the admin token for OAuth/SAML and add audit logging
- Connect Slack/Teams reminder hooks and Stripe for billing
- Delete comments/sample data before moving to production

## License
MIT
