"""Subscription model."""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as PgEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Plan(str, Enum):
    starter = "starter"
    pro = "pro"
    enterprise = "enterprise"


class SubscriptionStatus(str, Enum):
    trialing = "trialing"
    active = "active"
    past_due = "past_due"
    canceled = "canceled"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False, index=True)
    stripe_customer: Mapped[str | None] = mapped_column(String(120), nullable=True)
    stripe_subscription: Mapped[str | None] = mapped_column(String(120), nullable=True)
    plan: Mapped[Plan | None] = mapped_column(PgEnum(Plan, name="plan"), nullable=True)
    seats: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[SubscriptionStatus | None] = mapped_column(
        PgEnum(SubscriptionStatus, name="subscription_status"), nullable=True
    )
    trial_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    org = relationship("Org", back_populates="subscriptions")
