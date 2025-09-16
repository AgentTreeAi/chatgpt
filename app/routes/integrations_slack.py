"""Slack integration endpoints."""
from __future__ import annotations

from datetime import timedelta
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_token, decode_token
from app.db import models
from app.dependencies import get_db, require_csrf, require_role
from app.services import slack as slack_service

router = APIRouter(prefix="/integrations/slack", tags=["slack"])

SCOPES = "chat:write,commands,incoming-webhook,channels:read"


class SlackChannelPayload(BaseModel):
    channel: str = Field(..., min_length=1)


@router.get("/install")
def start_install(
    request: Request,
    session: dict = Depends(require_role("org_admin")),
) -> RedirectResponse:
    settings = get_settings()
    if not settings.slack_client_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Slack not configured")

    redirect_uri = str(request.url_for("slack_callback"))
    state = create_token({"org_id": session["org_id"]}, expires_delta=timedelta(minutes=10))
    params = {
        "client_id": settings.slack_client_id,
        "scope": SCOPES,
        "redirect_uri": redirect_uri,
        "state": state,
    }
    url = "https://slack.com/oauth/v2/authorize?" + urlencode(params)
    return RedirectResponse(url=url)


@router.get("/oauth/callback")
def slack_callback(
    request: Request,
    code: str,
    state: str,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    try:
        payload = decode_token(state)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state token") from exc

    org_id = payload.get("org_id")
    if not org_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing org context")

    redirect_uri = str(request.url_for("slack_callback"))
    data = slack_service.oauth_access(code, redirect_uri)

    integration = (
        db.query(models.Integration)
        .filter(models.Integration.org_id == org_id, models.Integration.kind == models.IntegrationKind.slack)
        .one_or_none()
    )
    if not integration:
        integration = models.Integration(org_id=org_id, kind=models.IntegrationKind.slack)

    incoming = data.get("incoming_webhook", {})
    integration.status = "connected"
    integration.config_json = {
        "team_id": data.get("team", {}).get("id"),
        "team_name": data.get("team", {}).get("name"),
        "bot_token": data.get("access_token"),
        "channel": incoming.get("channel_id"),
    }
    db.add(integration)
    db.commit()

    return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)


@router.post("/channel", status_code=status.HTTP_200_OK)
def update_channel(
    payload: SlackChannelPayload,
    session: dict = Depends(require_role("org_admin")),
    db: Session = Depends(get_db),
    _: None = Depends(require_csrf),
) -> dict[str, str]:
    integration = (
        db.query(models.Integration)
        .filter(models.Integration.org_id == session["org_id"], models.Integration.kind == models.IntegrationKind.slack)
        .one_or_none()
    )
    if not integration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slack integration not installed")

    integration.config_json["channel"] = payload.channel
    db.add(integration)
    db.commit()

    return {"detail": "Slack channel updated"}


@router.post("/test", status_code=status.HTTP_202_ACCEPTED)
def send_test_message(
    session: dict = Depends(require_role("org_admin")),
    db: Session = Depends(get_db),
    _: None = Depends(require_csrf),
) -> dict[str, str]:
    integration = (
        db.query(models.Integration)
        .filter(models.Integration.org_id == session["org_id"], models.Integration.kind == models.IntegrationKind.slack)
        .one_or_none()
    )
    if not integration or integration.status != "connected":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slack integration not installed")

    token = integration.config_json.get("bot_token")
    channel = integration.config_json.get("channel")
    if not token or not channel:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Slack channel not configured")

    ok = slack_service.post_message(token, channel, "Test message from RMHT")
    if not ok:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to post to Slack")

    return {"detail": "Test message sent"}
