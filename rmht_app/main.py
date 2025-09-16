"""FastAPI application for the Remote-Team Mental Health Tracker (RMHT)."""
from __future__ import annotations

import hashlib
import os
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Dict, Iterable, List, Optional

from fastapi import Depends, FastAPI, Form, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker, selectinload

from . import integrations

DATABASE_URL = os.getenv("RMHT_DATABASE_URL", "sqlite:///./rmht.db")
ADMIN_TOKEN = os.getenv("RMHT_ADMIN_TOKEN", "changeme")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
Base = declarative_base()


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), unique=True, nullable=False)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    members = relationship("Member", back_populates="team", cascade="all, delete-orphan")
    checkins = relationship("CheckIn", back_populates="team", cascade="all, delete-orphan")


class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    display_name = Column(String(120), nullable=False)
    hashed_token = Column(String(64), unique=True, nullable=False, index=True)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    team = relationship("Team", back_populates="members")
    checkins = relationship("CheckIn", back_populates="member", cascade="all, delete-orphan")


class CheckIn(Base):
    __tablename__ = "checkins"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)
    mood = Column(Integer, nullable=False)
    stress = Column(Integer, nullable=False)
    workload = Column(Integer, default=2, nullable=False)
    comment = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    member = relationship("Member", back_populates="checkins")
    team = relationship("Team", back_populates="checkins")


app = FastAPI(title="Remote-Team Mental Health Tracker", version="0.1.0")
templates = Jinja2Templates(directory="rmht_app/templates")
templates.env.globals["app_name"] = "Remote-Team Mental Health Tracker"


def get_db() -> Iterable[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()


def mask_token(raw_token: str) -> str:
    token = raw_token.strip()
    if len(token) <= 4:
        return "••" + token[-2:]
    return token[:2] + "•••" + token[-2:]


def get_member_by_token(db: Session, token: str) -> Optional[Member]:
    hashed = hash_token(token)
    return db.query(Member).filter(Member.hashed_token == hashed, Member.active.is_(True)).one_or_none()


def ensure_tables() -> None:
    Base.metadata.create_all(bind=engine)


def seed_demo_data(db: Session) -> None:
    if db.query(Team).count():
        return

    team = Team(name="Remote Success", description="Pilot team for the RMHT demo")
    db.add(team)
    db.flush()

    demo_tokens = {
        "demo-alex": "Alex (NYC)",
        "demo-brook": "Brook (Berlin)",
        "demo-cam": "Cam (Remote)",
    }
    members: Dict[str, Member] = {}
    for raw_token, alias in demo_tokens.items():
        member = Member(
            team_id=team.id,
            display_name=alias,
            hashed_token=hash_token(raw_token),
        )
        db.add(member)
        members[raw_token] = member

    db.flush()

    now = datetime.utcnow()
    sample_entries = [
        ("demo-alex", 4, 2, 2, "Feeling productive after focus time."),
        ("demo-brook", 3, 3, 2, "Need more async updates across regions."),
        ("demo-cam", 2, 4, 3, "Burnout creeping in, juggling two launches."),
        ("demo-alex", 5, 2, 1, "Weekend off helped a lot!"),
        ("demo-brook", 3, 4, 3, "Meetings stacked late—need guardrails."),
    ]

    for days_ago, entry in enumerate(sample_entries[::-1]):
        token, mood, stress, workload, comment = entry
        created = now - timedelta(days=days_ago * 2)
        db.add(
            CheckIn(
                team_id=team.id,
                member_id=members[token].id,
                mood=mood,
                stress=stress,
                workload=workload,
                comment=comment,
                created_at=created,
            )
        )

    db.commit()


@app.on_event("startup")
def on_startup() -> None:
    ensure_tables()
    with SessionLocal() as db:
        seed_demo_data(db)


@app.get("/", name="home", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    teams = db.query(Team).order_by(Team.created_at.asc()).all()
    context = {"request": request, "teams": teams}
    return templates.TemplateResponse("home.html", context)


@app.get("/checkin/{token}", name="checkin_form", response_class=HTMLResponse)
def checkin_form(
    request: Request,
    token: str,
    submitted: Optional[int] = Query(None),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    member = get_member_by_token(db, token)
    if not member:
        context = {"request": request, "invalid": True}
        return templates.TemplateResponse("checkin_form.html", context, status_code=status.HTTP_404_NOT_FOUND)

    context = {
        "request": request,
        "invalid": False,
        "submitted": bool(submitted),
        "team_name": member.team.name,
        "masked_token": mask_token(token),
    }
    return templates.TemplateResponse("checkin_form.html", context)


@app.post("/checkin/{token}", response_class=HTMLResponse)
def submit_checkin(
    request: Request,
    token: str,
    mood: int = Form(...),
    stress: int = Form(...),
    workload: int = Form(2),
    comment: str = Form(""),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    member = get_member_by_token(db, token)
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not recognized")

    checkin = CheckIn(
        team_id=member.team_id,
        member_id=member.id,
        mood=int(mood),
        stress=int(stress),
        workload=int(workload),
        comment=comment.strip(),
    )
    db.add(checkin)
    db.commit()

    redirect_url = str(request.url.include_query_params(submitted=1))
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)


def _trend_chart(checkins: List[CheckIn]) -> Dict[str, List[float]]:
    buckets: Dict[date, Dict[str, List[int]]] = defaultdict(lambda: {"mood": [], "stress": []})
    for checkin in checkins:
        day = checkin.created_at.date()
        buckets[day]["mood"].append(checkin.mood)
        buckets[day]["stress"].append(checkin.stress)

    labels: List[str] = []
    mood_values: List[float] = []
    stress_values: List[float] = []

    for day in sorted(buckets):
        labels.append(day.strftime("%b %d"))
        mood_values.append(sum(buckets[day]["mood"]) / len(buckets[day]["mood"]))
        stress_values.append(sum(buckets[day]["stress"]) / len(buckets[day]["stress"]))

    return {"labels": labels, "mood": mood_values, "stress": stress_values}


def _participation_rate(db: Session, team_id: int) -> float:
    member_count = db.query(Member).filter(Member.team_id == team_id, Member.active.is_(True)).count()
    if not member_count:
        return 0.0

    start = datetime.utcnow() - timedelta(days=7)
    participants = (
        db.query(CheckIn.member_id)
        .filter(CheckIn.team_id == team_id, CheckIn.created_at >= start)
        .distinct()
        .count()
    )
    return (participants / member_count) * 100


def _risk_level(avg_stress: float, participation_rate: float) -> str:
    if avg_stress >= 4 or participation_rate < 30:
        return "High"
    if avg_stress >= 3.3 or participation_rate < 50:
        return "Elevated"
    return "Stable"


def _signals(avg_mood: float, avg_stress: float, participation_rate: float) -> List[Dict[str, str]]:
    signals: List[Dict[str, str]] = []
    if avg_stress >= 4:
        signals.append({"status": "critical", "message": "Stress is trending high—consider a reset."})
    elif avg_stress >= 3.3:
        signals.append({"status": "watch", "message": "Stress elevated. Encourage focus time and async updates."})
    else:
        signals.append({"status": "ok", "message": "Stress levels look manageable right now."})

    if avg_mood < 3:
        signals.append({"status": "watch", "message": "Mood is dipping. Facilitate peer recognition or check-ins."})
    else:
        signals.append({"status": "ok", "message": "Mood trending positively."})

    if participation_rate < 40:
        signals.append({"status": "watch", "message": "Participation is low—send a gentle Slack or Teams reminder."})
    else:
        signals.append({"status": "ok", "message": "Participation healthy."})

    return signals


@app.get("/dashboard/{team_id}", name="dashboard", response_class=HTMLResponse)
def dashboard(request: Request, team_id: int, db: Session = Depends(get_db)) -> HTMLResponse:
    team = (
        db.query(Team)
        .options(selectinload(Team.members).selectinload(Member.checkins))
        .filter(Team.id == team_id)
        .one_or_none()
    )
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    window_start = datetime.utcnow() - timedelta(days=14)
    checkins = (
        db.query(CheckIn)
        .filter(CheckIn.team_id == team_id, CheckIn.created_at >= window_start)
        .order_by(CheckIn.created_at.asc())
        .all()
    )

    if checkins:
        average_mood = sum(c.mood for c in checkins) / len(checkins)
        average_stress = sum(c.stress for c in checkins) / len(checkins)
    else:
        average_mood = 0.0
        average_stress = 0.0

    participation_rate = _participation_rate(db, team_id)
    risk_level = _risk_level(average_stress, participation_rate)
    signals = _signals(average_mood, average_stress, participation_rate)

    latest_checkins = (
        db.query(CheckIn)
        .filter(CheckIn.team_id == team_id)
        .order_by(CheckIn.created_at.desc())
        .limit(5)
        .all()
    )

    chart_config = _trend_chart(checkins)

    workload_labels = {1: "Light", 2: "Balanced", 3: "Heavy"}
    latest_payload = [
        {
            "created_at": item.created_at,
            "comment": item.comment,
            "mood": item.mood,
            "stress": item.stress,
            "workload_label": workload_labels.get(item.workload, "Balanced"),
            "member_alias": item.member.display_name,
        }
        for item in latest_checkins
    ]

    calendar_stats = integrations.fetch_calendar_stats(team.name)
    roster = [
        {"display_name": member.display_name, "checkin_count": len(member.checkins)}
        for member in team.members
    ]

    context = {
        "request": request,
        "team": team,
        "average_mood": average_mood,
        "average_stress": average_stress,
        "participation_rate": participation_rate,
        "risk_level": risk_level,
        "signals": signals,
        "chart_config": chart_config,
        "latest_checkins": latest_payload,
        "calendar_stats": calendar_stats,
        "base_url": str(request.base_url).rstrip("/"),
        "roster": roster,
    }
    return templates.TemplateResponse("dashboard.html", context)


@app.get("/admin", name="admin_portal", response_class=HTMLResponse)
def admin_portal(
    request: Request,
    token: str = Query(...),
    message: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin token")

    teams = (
        db.query(Team)
        .options(
            selectinload(Team.members),
            selectinload(Team.checkins),
        )
        .order_by(Team.created_at.asc())
        .all()
    )
    context = {
        "request": request,
        "teams": teams,
        "admin_token": token,
        "message": message,
    }
    return templates.TemplateResponse("admin.html", context)


@app.post("/admin/team", name="create_team")
def create_team(
    request: Request,
    admin_token: str = Form(...),
    team_name: str = Form(...),
    team_description: str = Form(""),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    if admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin token")

    team = Team(name=team_name.strip(), description=team_description.strip())
    db.add(team)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Team name already exists")

    redirect_url = request.url_for("admin_portal") + f"?token={admin_token}&message=Team%20created"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)


@app.post("/admin/member", name="create_member")
def create_member(
    request: Request,
    admin_token: str = Form(...),
    display_name: str = Form(...),
    token: str = Form(...),
    team_id: int = Form(...),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    if admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin token")

    member = Member(
        team_id=int(team_id),
        display_name=display_name.strip(),
        hashed_token=hash_token(token),
    )
    db.add(member)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token already exists")

    redirect_url = request.url_for("admin_portal") + f"?token={admin_token}&message=Token%20created"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)


@app.get("/healthz")
def healthcheck() -> Dict[str, str]:
    return {"status": "ok"}
