"""Risk scoring helpers."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from math import sqrt

from sqlalchemy.orm import Session

from app.db.models import Checkin, RiskLevel, RiskSnapshot, Team


def ewma(values: list[float], span: int = 30) -> float:
    if not values:
        return 0.0
    alpha = 2 / (span + 1)
    result = values[0]
    for value in values[1:]:
        result = alpha * value + (1 - alpha) * result
    return result


def latest_risk_snapshot(db: Session, team: Team) -> RiskSnapshot:
    today = date.today()
    start = today - timedelta(days=30)

    daily: dict[date, list[tuple[int, int]]] = defaultdict(list)
    rows = (
        db.query(Checkin.checkin_date, Checkin.mood, Checkin.stress)
        .filter(Checkin.team_id == team.id, Checkin.checkin_date >= start)
        .all()
    )
    for checkin_date, mood, stress in rows:
        daily[checkin_date].append((mood, stress))

    if not rows:
        return RiskSnapshot(
            team_id=team.id,
            day=today,
            risk_level=RiskLevel.low,
            avg_mood=0,
            avg_stress=0,
            checkin_count=0,
        )

    ordered_days = sorted(daily.keys())
    stress_averages: list[float] = []
    mood_averages: list[float] = []
    counts: list[int] = []

    for day in ordered_days:
        entries = daily[day]
        moods = [m for m, _ in entries]
        stresses = [s for _, s in entries]
        stress_avg = sum(stresses) / len(stresses)
        mood_avg = sum(moods) / len(moods)
        stress_averages.append(stress_avg)
        mood_averages.append(mood_avg)
        counts.append(len(entries))

    stress_ewma = ewma(stress_averages)
    avg_mood = sum(mood_averages[-7:]) / min(len(mood_averages), 7)
    avg_stress = sum(stress_averages[-7:]) / min(len(stress_averages), 7)
    recent_count = sum(counts[-7:])
    prior_count = sum(counts[-14:-7]) if len(counts) >= 14 else sum(counts[:-7])
    participation_drop = recent_count < 5 or (prior_count and recent_count < prior_count * 0.6)

    recent_avg = sum(stress_averages[-7:]) / min(len(stress_averages), 7)
    prev_avg = sum(stress_averages[-14:-7]) / 7 if len(stress_averages) >= 14 else recent_avg
    delta = recent_avg - prev_avg

    mean_stress = sum(stress_averages) / len(stress_averages)
    variance = sum((s - mean_stress) ** 2 for s in stress_averages) / max(len(stress_averages), 1)
    stdev = sqrt(variance)
    z_score = (stress_ewma - mean_stress) / stdev if stdev else 0

    signals = 0
    if stress_ewma > mean_stress + 0.5:
        signals += 1
    if delta > 0.3:
        signals += 1
    if participation_drop:
        signals += 1

    if z_score > 1.7 or signals >= 3:
        level = RiskLevel.high
    elif signals >= 2:
        level = RiskLevel.moderate
    else:
        level = RiskLevel.low

    snapshot = RiskSnapshot(
        team_id=team.id,
        day=today,
        risk_level=level,
        avg_mood=avg_mood,
        avg_stress=avg_stress,
        checkin_count=sum(counts[-7:]),
    )
    return snapshot


def upsert_risk_snapshot(db: Session, team: Team) -> RiskSnapshot:
    snapshot = latest_risk_snapshot(db, team)
    existing = (
        db.query(RiskSnapshot)
        .filter(RiskSnapshot.team_id == team.id, RiskSnapshot.day == snapshot.day)
        .one_or_none()
    )
    if existing:
        existing.risk_level = snapshot.risk_level
        existing.avg_mood = snapshot.avg_mood
        existing.avg_stress = snapshot.avg_stress
        existing.checkin_count = snapshot.checkin_count
        db.add(existing)
        return existing

    db.add(snapshot)
    return snapshot
