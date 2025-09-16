"""Public marketing and participant routes."""
from __future__ import annotations

import hashlib
from datetime import date, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import models
from app.dependencies import get_db
from app.services import analytics, risk

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
templates.env.globals["app_name"] = "Remote-Team Mental Health Tracker"


def hash_token(token: str) -> str:
    return hashlib.sha256(token.strip().encode("utf-8")).hexdigest()


def mask_token(token: str) -> str:
    token = token.strip()
    if len(token) <= 4:
        return "••" + token[-2:]
    return token[:2] + "•••" + token[-2:]


@router.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("home.html", {"request": request})


@router.get("/checkin/{token}", response_class=HTMLResponse)
def get_checkin(
    token: str,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> HTMLResponse:
    hashed = hash_token(token)
    user = db.query(models.User).filter(models.User.anon_token_hash == hashed, models.User.active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid token")

    return templates.TemplateResponse(
        "checkin_form.html",
        {
            "request": request,
            "team": user.team,
            "token_masked": mask_token(token),
        },
    )


@router.post("/checkin/{token}")
def submit_checkin(
    token: str,
    mood: Annotated[int, Form(...)],
    stress: Annotated[int, Form(...)],
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    comment: Annotated[str | None, Form()] = "",
) -> HTMLResponse:
    hashed = hash_token(token)
    user = db.query(models.User).filter(models.User.anon_token_hash == hashed, models.User.active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid token")

    if not (1 <= mood <= 5 and 1 <= stress <= 5):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Scores must be 1-5")

    checkin = models.Checkin(
        user_id=user.id,
        team_id=user.team_id,
        mood=mood,
        stress=stress,
        comment=comment or "",
        checkin_date=date.today(),
        submitted_at=datetime.utcnow(),
    )
    db.add(checkin)
    db.flush()

    risk.upsert_risk_snapshot(db, user.team)
    db.commit()

    return templates.TemplateResponse(
        "checkin_form.html",
        {
            "request": request,
            "team": user.team,
            "token_masked": mask_token(token),
            "success": True,
        },
    )


@router.get("/dashboard/{team_id}", response_class=HTMLResponse)
def dashboard(
    team_id: int,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> HTMLResponse:
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    metrics = analytics.team_metrics(db, team)
    if not metrics.get("available"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough data to show dashboard")

    recent_days = date.today() - timedelta(days=14)
    trends = (
        db.query(
            models.Checkin.checkin_date,
            func.avg(models.Checkin.mood),
            func.avg(models.Checkin.stress),
        )
        .filter(models.Checkin.team_id == team.id, models.Checkin.checkin_date >= recent_days)
        .group_by(models.Checkin.checkin_date)
        .order_by(models.Checkin.checkin_date)
        .all()
    )

    chart_config = {
        "labels": [row[0].strftime("%b %d") for row in trends],
        "mood": [round(float(row[1]), 2) for row in trends],
        "stress": [round(float(row[2]), 2) for row in trends],
    }

    active_users = db.query(models.User).filter(models.User.team_id == team.id, models.User.active.is_(True)).count()
    participation_base = active_users if active_users else 1
    last_week = date.today() - timedelta(days=7)
    participation = (
        db.query(func.count(models.Checkin.id))
        .filter(models.Checkin.team_id == team.id, models.Checkin.checkin_date >= last_week)
        .scalar()
    ) or 0
    participation_rate = min(100.0, (participation / participation_base) * 100)

    latest_checkins = (
        db.query(models.Checkin)
        .filter(models.Checkin.team_id == team.id)
        .order_by(models.Checkin.submitted_at.desc())
        .limit(5)
        .all()
    )

    roster_counts = (
        db.query(models.User.id, models.User.email, func.count(models.Checkin.id))
        .outerjoin(models.Checkin, models.Checkin.user_id == models.User.id)
        .filter(models.User.team_id == team.id)
        .group_by(models.User.id)
        .all()
    )

    signals = []
    avg_stress_value = metrics.get("avg_stress")
    if isinstance(avg_stress_value, (int, float)) and avg_stress_value >= 3.5:
        signals.append({"status": "critical", "message": "Stress trending high vs. target"})
    if participation_rate < 70:
        signals.append({"status": "watch", "message": "Participation below 70% of active seats"})

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "team": team,
            "average_mood": metrics.get("avg_mood", 0),
            "average_stress": metrics.get("avg_stress", 0),
            "participation_rate": participation_rate,
            "chart_config": chart_config,
            "signals": signals,
            "latest_checkins": latest_checkins,
            "roster": roster_counts,
            "risk_level": str(metrics.get("risk_level") or "low").capitalize(),
            "base_url": str(request.base_url).rstrip("/"),
        },
    )
