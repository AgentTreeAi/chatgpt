"""Integration stubs for RMHT micro-SaaS."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class PromptResult:
    channel: str
    scheduled_for: dt.datetime
    status: str
    detail: str


def send_slack_prompt(team_name: str, message: str) -> PromptResult:
    """Pretend to send a Slack message asking the team to complete check-ins."""
    return PromptResult(
        channel="slack",
        scheduled_for=dt.datetime.utcnow(),
        status="scheduled",
        detail=f"Would send to Slack channel for team '{team_name}': {message}",
    )


def send_teams_prompt(team_name: str, message: str) -> PromptResult:
    """Pretend to send a Microsoft Teams adaptive card."""
    return PromptResult(
        channel="teams",
        scheduled_for=dt.datetime.utcnow(),
        status="scheduled",
        detail=f"Would send to Teams channel for team '{team_name}': {message}",
    )


def fetch_calendar_stats(team_name: str) -> Dict[str, Any]:
    """Mock calendar utilization stats."""
    today = dt.date.today()
    return {
        "team": team_name,
        "week_start": today - dt.timedelta(days=today.weekday()),
        "focus_time_hours": 12,
        "meeting_hours": 18,
        "avg_after_hours": 1.5,
    }


def sync_hris_data() -> List[Dict[str, Any]]:
    """Pretend to sync HRIS employee roster."""
    return [
        {"employee_id": "demo-001", "status": "active"},
        {"employee_id": "demo-002", "status": "active"},
    ]


__all__ = [
    "PromptResult",
    "send_slack_prompt",
    "send_teams_prompt",
    "fetch_calendar_stats",
    "sync_hris_data",
]
