"""Slack integration helpers."""
from __future__ import annotations

import logging
from typing import Any, Dict

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)
SLACK_API_BASE = "https://slack.com/api"


def oauth_access(code: str, redirect_uri: str) -> Dict[str, Any]:
    settings = get_settings()
    if not settings.slack_client_id or not settings.slack_client_secret:
        raise RuntimeError("Slack client not configured")

    payload = {
        "code": code,
        "client_id": settings.slack_client_id,
        "client_secret": settings.slack_client_secret,
        "redirect_uri": redirect_uri,
    }
    with httpx.Client(timeout=10) as client:
        resp = client.post(f"{SLACK_API_BASE}/oauth.v2.access", data=payload)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            logger.error("Slack OAuth error: %s", data)
            raise RuntimeError(data.get("error", "Slack OAuth failed"))
        return data


def post_message(token: str, channel: str, text: str) -> bool:
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"}
    payload = {"channel": channel, "text": text}
    with httpx.Client(timeout=10) as client:
        resp = client.post(f"{SLACK_API_BASE}/chat.postMessage", json=payload, headers=headers)
        if resp.status_code >= 400:
            logger.error("Slack postMessage HTTP %s: %s", resp.status_code, resp.text)
            return False
        body = resp.json()
        if not body.get("ok"):
            logger.error("Slack postMessage response: %s", body)
            return False
    return True
