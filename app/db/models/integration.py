"""Integration model."""
from __future__ import annotations

from enum import Enum
from typing import Any

from sqlalchemy import Enum as PgEnum, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class IntegrationKind(str, Enum):
    slack = "slack"
    calendar = "calendar"
    hris = "hris"


class Integration(Base):
    __tablename__ = "integrations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False, index=True)
    kind: Mapped[IntegrationKind] = mapped_column(PgEnum(IntegrationKind, name="integration_kind"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="disconnected", nullable=False)
    config_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    org = relationship("Org", back_populates="integrations")
