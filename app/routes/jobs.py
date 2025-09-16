"""Background job endpoints triggered by Railway cron."""
from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import models
from app.dependencies import get_db
from app.services import billing as billing_service
from app.services import slack as slack_service

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _verify_secret(secret: str | None) -> None:
    settings = get_settings()
    if not settings.cron_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cron secret not configured")
    if secret != settings.cron_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid cron secret")


@router.post("/weekly-checkin")
def weekly_checkin(
    request: Request,
    secret: str,
    db: Session = Depends(get_db),
) -> dict[str, int]:
    _verify_secret(secret)
    settings = get_settings()
    base_url = settings.app_base_url or str(request.base_url).rstrip("/")
    integrations = (
        db.query(models.Integration)
        .filter(models.Integration.kind == models.IntegrationKind.slack, models.Integration.status == "connected")
        .all()
    )

    posted = 0
    for integration in integrations:
        token = integration.config_json.get("bot_token")
        channel = integration.config_json.get("channel")
        if not token or not channel:
            continue
        message = (
            "\u2705 It's time for your weekly RMHT check-in! Use your personal token at "
            f"{base_url}/checkin/<token> to share mood & stress in under 60 seconds."
        )
        if slack_service.post_message(token, channel, message):
            posted += 1

    return {"orgs_notified": posted, "total_integrations": len(integrations)}


@router.post("/daily-retention")
def daily_retention(
    secret: str,
    db: Session = Depends(get_db),
) -> dict[str, int]:
    _verify_secret(secret)
    removed = 0
    today = date.today()
    teams = db.query(models.Team).all()
    for team in teams:
        retention_days = team.org.retention_days if team.org else 180
        cutoff = today - timedelta(days=retention_days)
        deleted = (
            db.query(models.Checkin)
            .filter(models.Checkin.team_id == team.id, models.Checkin.checkin_date < cutoff)
            .delete(synchronize_session=False)
        )
        removed += deleted
    db.commit()
    return {"checkins_removed": removed}


@router.post("/sync-seats")
def sync_seats(
    secret: str,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    _verify_secret(secret)
    try:
        billing_service.sync_subscription_seats(db)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return {"status": "synced"}
