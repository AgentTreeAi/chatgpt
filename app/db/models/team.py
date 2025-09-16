"""Team model."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    org = relationship("Org", back_populates="teams")
    users = relationship("User", back_populates="team", cascade="all, delete-orphan")
    checkins = relationship("Checkin", back_populates="team", cascade="all, delete-orphan")
    calendar_stats = relationship("CalendarStat", back_populates="team", cascade="all, delete-orphan")
    risk_snapshots = relationship("RiskSnapshot", back_populates="team", cascade="all, delete-orphan")
