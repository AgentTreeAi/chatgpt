"""Risk snapshot model."""
from __future__ import annotations

from datetime import date
from enum import Enum

from sqlalchemy import Date, Enum as PgEnum, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RiskLevel(str, Enum):
    low = "low"
    moderate = "moderate"
    high = "high"


class RiskSnapshot(Base):
    __tablename__ = "risk_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    day: Mapped[date] = mapped_column(Date, nullable=False)
    risk_level: Mapped[RiskLevel] = mapped_column(PgEnum(RiskLevel, name="risk_level"), nullable=False)
    avg_mood: Mapped[float] = mapped_column(Float, nullable=False)
    avg_stress: Mapped[float] = mapped_column(Float, nullable=False)
    checkin_count: Mapped[int] = mapped_column(Integer, nullable=False)

    team = relationship("Team", back_populates="risk_snapshots")
