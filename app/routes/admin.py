"""Admin routes with RBAC and org scoping."""
from __future__ import annotations

import hashlib

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import models
from app.dependencies import get_db, require_csrf, require_role
from app.services import analytics

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="app/templates")
templates.env.globals["app_name"] = "Remote-Team Mental Health Tracker"

ALLOWED_ROLES = {"org_admin", "team_lead", "employee"}


class CreateTeamRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)


class CreateUserRequest(BaseModel):
    team_id: int
    email: EmailStr | None = None
    token: str = Field(..., min_length=6)
    role: str = Field(default="employee")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "team_id": 1,
                    "email": "alex@example.com",
                    "token": "demo-alex",
                    "role": "employee",
                }
            ]
        }


@router.get("", response_class=HTMLResponse)
def admin_home(
    request: Request,
    session: dict = Depends(require_role("org_admin", "team_lead")),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    org = db.query(models.Org).filter(models.Org.id == session["org_id"]).one()

    teams_query = db.query(models.Team).filter(models.Team.org_id == org.id)
    if session.get("role") == "team_lead":
        teams_query = teams_query.filter(models.Team.id == session.get("team_id"))
    teams = teams_query.order_by(models.Team.name).all()

    team_data = [
        {
            "team": team,
            "metrics": analytics.team_metrics(db, team),
        }
        for team in teams
    ]

    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "org": org,
            "teams": team_data,
            "session": session,
        },
    )


@router.post("/teams", status_code=status.HTTP_201_CREATED)
def create_team(
    payload: CreateTeamRequest,
    session: dict = Depends(require_role("org_admin")),
    db: Session = Depends(get_db),
    _: None = Depends(require_csrf),
) -> dict[str, int | str]:
    exists = (
        db.query(models.Team)
        .filter(models.Team.org_id == session["org_id"], func.lower(models.Team.name) == payload.name.lower())
        .first()
    )
    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Team already exists")

    team = models.Team(org_id=session["org_id"], name=payload.name)
    db.add(team)
    db.flush()

    audit = models.AuditLog(
        org_id=session["org_id"],
        actor=str(session.get("user_id")),
        action="create_team",
        target=payload.name,
        meta_json={"team_id": team.id},
    )
    db.add(audit)
    db.commit()

    return {"id": team.id, "name": team.name}


@router.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(
    payload: CreateUserRequest,
    session: dict = Depends(require_role("org_admin", "team_lead")),
    db: Session = Depends(get_db),
    _: None = Depends(require_csrf),
) -> dict[str, int | str]:
    if payload.role not in ALLOWED_ROLES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")

    team = (
        db.query(models.Team)
        .filter(models.Team.id == payload.team_id, models.Team.org_id == session["org_id"])
        .one_or_none()
    )
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    if session.get("role") == "team_lead" and team.id != session.get("team_id"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot manage other teams")

    hashed = hashlib.sha256(payload.token.strip().encode("utf-8")).hexdigest()
    if db.query(models.User).filter(models.User.anon_token_hash == hashed).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token already assigned")

    user = models.User(
        team_id=team.id,
        email=payload.email.lower() if payload.email else None,
        anon_token_hash=hashed,
        role=payload.role,
    )
    db.add(user)
    db.flush()

    audit = models.AuditLog(
        org_id=session["org_id"],
        actor=str(session.get("user_id")),
        action="create_user",
        target=payload.email,
        meta_json={"user_id": user.id, "team_id": team.id},
    )
    db.add(audit)
    db.commit()

    return {"id": user.id, "team_id": user.team_id, "email": user.email, "role": user.role}
