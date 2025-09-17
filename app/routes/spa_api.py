"""JSON APIs backing the Vite-powered SPA."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any, TypedDict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import models
from app.dependencies import get_db
from app.services import analytics, risk

router = APIRouter(prefix="/api", tags=["spa"])

class _SampleSeries(TypedDict):
    name: str
    data: list[int]


_SAMPLE_SERIES: list[_SampleSeries] = [
    {"name": "Mood", "data": [72, 68, 74, 70, 75, 77, 80]},
    {"name": "Stress", "data": [45, 50, 48, 52, 49, 47, 44]},
]
_SAMPLE_HIGHLIGHTS = [
    "Team engagement trending upward week over week",
    "Stress reports declining following wellness initiative",
    "Upcoming leadership AMA scheduled for Friday",
]


class _SampleSummary(TypedDict):
    risk_level: str
    participation: int
    sentiment: int
    active_rituals: int
    highlights: list[str]
    source: str


_SAMPLE_SUMMARY: _SampleSummary = {
    "risk_level": "low",
    "participation": 78,
    "sentiment": 74,
    "active_rituals": 4,
    "highlights": _SAMPLE_HIGHLIGHTS,
    "source": "sample",
}


def _sample_dashboard() -> dict[str, Any]:
    """Return a deep copy of the canned dashboard payload."""

    return {
        "series": [
            {"name": entry["name"], "data": entry["data"].copy()} for entry in _SAMPLE_SERIES
        ],
        "summary": {**_SAMPLE_SUMMARY, "highlights": _SAMPLE_SUMMARY["highlights"].copy()},
    }


def _percent(value: float | None, scale: int = 5) -> int:
    if value is None:
        return 0
    return int(round((value / scale) * 100))


@router.get("/dashboard/{team_id}")
def fetch_dashboard(
    team_id: str,
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Return aggregated dashboard metrics for the requested team."""

    # Allow public demo payload without authentication.
    if team_id.lower() == "demo":
        return _sample_dashboard()

    session = request.session or {}
    if "user_id" not in session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    if session.get("role") not in {"org_admin", "team_lead"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")

    try:
        team_id_int = int(team_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found") from exc

    team = (
        db.query(models.Team)
        .filter(models.Team.id == team_id_int, models.Team.org_id == session.get("org_id"))
        .first()
    )
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    if session.get("role") == "team_lead" and session.get("team_id") != team.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot access other teams")

    metrics = analytics.team_metrics(db, team)
    if not metrics.get("available"):
        payload = _sample_dashboard()
        payload["summary"]["detail"] = "Sample data shown until ≥5 weekly respondents participate."
        return payload

    start_date = date.today() - timedelta(days=6)
    days = [start_date + timedelta(days=offset) for offset in range(7)]

    rows = (
        db.query(models.Checkin.checkin_date, func.avg(models.Checkin.mood), func.avg(models.Checkin.stress))
        .filter(models.Checkin.team_id == team.id, models.Checkin.checkin_date >= start_date)
        .group_by(models.Checkin.checkin_date)
        .all()
    )

    daily = {row[0]: (float(row[1]), float(row[2])) for row in rows}

    mood_series: list[int | None] = []
    stress_series: list[int | None] = []
    for day in days:
        mood_value, stress_value = daily.get(day, (None, None))
        mood_series.append(_percent(mood_value) if mood_value is not None else None)
        stress_series.append(_percent(stress_value) if stress_value is not None else None)

    active_users = (
        db.query(models.User)
        .filter(models.User.team_id == team.id, models.User.active.is_(True))
        .count()
    )
    last_week = date.today() - timedelta(days=7)
    completed = (
        db.query(func.count(models.Checkin.id))
        .filter(models.Checkin.team_id == team.id, models.Checkin.checkin_date >= last_week)
        .scalar()
    ) or 0
    participation = 0
    if active_users:
        participation = int(round(min(completed / active_users, 1.0) * 100))

    avg_mood_metric = metrics.get("avg_mood")
    sentiment = (
        _percent(float(avg_mood_metric))
        if isinstance(avg_mood_metric, (int, float))
        else 0
    )
    avg_stress_metric = metrics.get("avg_stress")
    avg_stress = (
        float(avg_stress_metric) if isinstance(avg_stress_metric, (int, float)) else None
    )
    risk_snapshot = risk.latest_risk_snapshot(db, team)
    risk_level_value = metrics.get("risk_level")
    if not risk_level_value and risk_snapshot:
        risk_level_value = risk_snapshot.risk_level.value
    risk_level = str(risk_level_value or "low").lower()

    highlights: list[str] = []
    if participation < 70:
        highlights.append("Participation dipped under 70% — consider a friendly mid-week reminder.")
    if sentiment >= 80:
        highlights.append("Mood is trending upbeat — celebrate wins in the next async retro.")
    elif sentiment <= 50:
        highlights.append("Mood is sliding — schedule a wellbeing check-in with the team.")
    if avg_stress is not None and avg_stress >= 3.5:
        highlights.append("Stress is elevated; rebalance workloads or extend focus time blocks.")
    if risk_level == "high":
        highlights.append("Risk level is high — escalate to leadership for quick support.")
    elif risk_level == "moderate":
        highlights.append("Risk is climbing — reinforce rituals and monitor closely this week.")
    if not highlights:
        highlights.append("Ritual cadence is steady — keep nudging async updates and kudos.")

    payload = {
        "series": [
            {"name": "Mood", "data": mood_series},
            {"name": "Stress", "data": stress_series},
        ],
        "summary": {
            "risk_level": risk_level,
            "participation": participation,
            "sentiment": sentiment,
            "active_rituals": 4,
            "highlights": highlights,
            "respondents": metrics.get("respondent_count", 0),
            "team": {"id": team.id, "name": team.name},
            "source": "live",
        },
    }

    settings = get_settings()
    if settings.app_env != "production":
        payload["summary"]["detail"] = "Live metrics from development dataset."

    return payload
