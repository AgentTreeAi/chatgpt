"""FastAPI application entry point for RMHT."""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.engine import make_url
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import get_settings
from app.middleware import RequestIDMiddleware
from app.db import models
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.routes import admin, auth, billing_stripe, health, integrations_slack, jobs, public
from app.services import risk as risk_service

logging.basicConfig(
    level=logging.INFO,
    format="{\"timestamp\":\"%(asctime)s\",\"level\":\"%(levelname)s\",\"message\":\"%(message)s\",\"logger\":\"%(name)s\"}",
)

settings = get_settings()
logger = logging.getLogger(__name__)

app = FastAPI(title="Remote-Team Mental Health Tracker", version="1.0.0")

app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    SessionMiddleware, 
    secret_key=settings.secret_key, 
    https_only=(settings.app_env == "prod"), 
    max_age=60 * 60 * 24 * 7, 
    same_site="lax"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_cors_origins,
    allow_credentials=("*" not in settings.allowed_cors_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(public.router)
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(integrations_slack.router)
app.include_router(billing_stripe.router)
app.include_router(jobs.router)


def describe_database(url: str) -> str:
    """Return a human-friendly description of the configured database."""

    if url.startswith("sqlite"):
        return f"SQLite ({url})"

    try:
        parsed = make_url(url)
    except Exception:
        return "Database URL configured"

    return parsed.render_as_string(hide_password=True)


@app.on_event("startup")
def ensure_seed_data() -> None:
    """Create demo data for local development only."""

    logger.info("Starting RMHT application (env=%s)", settings.app_env)

    try:
        database_url = settings.resolved_database_url
    except ValueError as exc:
        logger.error("Database configuration error: %s", exc)
        raise

    logger.info("Using database %s", describe_database(database_url))

    # Only create tables and seed data in development
    if settings.app_env != "prod":
        Base.metadata.create_all(bind=engine)
        
        with SessionLocal() as session:
            if session.query(models.Org).count():
                return

            org = models.Org(name="Demo Org", allowed_domains=["example.com"])
            session.add(org)
            session.flush()

            team = models.Team(org_id=org.id, name="Remote Success")
            session.add(team)
            session.flush()

            demo_token = "demo-token"
            hashed = hashlib.sha256(demo_token.encode("utf-8")).hexdigest()
            user = models.User(team_id=team.id, anon_token_hash=hashed, email="demo@example.com", role="team_lead")
            session.add(user)
            session.flush()

            now = datetime.utcnow()
            samples = [
                (4, 2, "Feeling focused after maker time."),
                (3, 3, "Juggling async updates across zones."),
                (2, 4, "Need support to avoid burnout."),
                (5, 2, "Recharge weekend helped a ton."),
                (3, 4, "Meetings late in the day again."),
            ]
            for idx, (mood, stress, comment) in enumerate(samples):
                session.add(
                    models.Checkin(
                        user_id=user.id,
                        team_id=team.id,
                        mood=mood,
                        stress=stress,
                        comment=comment,
                        submitted_at=now - timedelta(days=idx),
                        checkin_date=(now - timedelta(days=idx)).date(),
                    )
                )

            risk_service.upsert_risk_snapshot(session, team)
            session.commit()
