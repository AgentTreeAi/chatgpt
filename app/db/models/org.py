"""Org model definition."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Org(Base):
    """Represents a customer organization."""

    __tablename__ = "orgs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    allowed_domains: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    retention_days: Mapped[int] = mapped_column(Integer, default=180, nullable=False)

    teams = relationship("Team", back_populates="org", cascade="all, delete-orphan")
    integrations = relationship("Integration", back_populates="org", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="org", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="org", cascade="all, delete-orphan")
