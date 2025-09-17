"""Analytics helpers for dashboards."""
from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Checkin, RiskSnapshot, Team

MINIMUM_RESPONDENTS = 5


def team_metrics(db: Session, team: Team) -> dict[str, float | int | str | None | bool]:
    """Compute aggregated team metrics enforcing anonymity thresholds."""

    cutoff = date.today() - timedelta(days=30)
    stmt = (
        select(
            func.count(Checkin.id),
            func.avg(Checkin.mood),
            func.avg(Checkin.stress),
        )
        .where(Checkin.team_id == team.id, Checkin.checkin_date >= cutoff)
    )
    total, avg_mood, avg_stress = db.execute(stmt).one()
    if total is None or total < MINIMUM_RESPONDENTS:
        return {"available": False, "respondent_count": total or 0}

    risk = (
        db.query(RiskSnapshot)
        .filter(RiskSnapshot.team_id == team.id)
        .order_by(RiskSnapshot.day.desc())
        .first()
    )

    return {
        "available": True,
        "respondent_count": int(total),
        "avg_mood": float(avg_mood) if avg_mood is not None else None,
        "avg_stress": float(avg_stress) if avg_stress is not None else None,
        "risk_level": risk.risk_level.value if risk else None,
    }
