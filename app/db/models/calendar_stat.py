"""Calendar stats model."""
from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CalendarStat(Base):
    __tablename__ = "calendar_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    day: Mapped[date] = mapped_column(Date, nullable=False)
    meeting_hours: Mapped[float] = mapped_column(Float, nullable=False)
    after_hours_events: Mapped[int] = mapped_column(Integer, nullable=False)

    team = relationship("Team", back_populates="calendar_stats")
