"""Stripe billing helpers."""
from __future__ import annotations

import logging

import stripe
from typing import cast

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Plan, Subscription, SubscriptionStatus, User

logger = logging.getLogger(__name__)


def _configure_stripe() -> None:
    settings = get_settings()
    if not settings.stripe_secret_key:
        raise RuntimeError("STRIPE_SECRET_KEY not configured")
    stripe.api_key = settings.stripe_secret_key


def _price_for_plan(plan: Plan) -> str:
    settings = get_settings()
    mapping = {
        Plan.starter: settings.stripe_price_starter,
        Plan.pro: settings.stripe_price_pro,
        Plan.enterprise: settings.stripe_price_enterprise,
    }
    price = mapping.get(plan)
    if price is None or price == "":
        raise RuntimeError(f"No Stripe price ID configured for {plan.value}")
    return cast(str, price)


def create_checkout_session(org_id: int, plan: Plan, quantity: int, success_url: str, cancel_url: str) -> str:
    _configure_stripe()
    session = stripe.checkout.Session.create(
        mode="subscription",
        success_url=success_url,
        cancel_url=cancel_url,
        customer_creation="always",
        line_items=[{"price": _price_for_plan(plan), "quantity": max(quantity, 1)}],
        subscription_data={
            "metadata": {"org_id": str(org_id)},
            "trial_period_days": 14,
        },
        metadata={"org_id": str(org_id)},
    )
    url = session.url
    if not url:
        raise RuntimeError("Stripe checkout session did not include a URL")
    return str(url)


def create_billing_portal(stripe_customer: str, return_url: str) -> str:
    _configure_stripe()
    portal = stripe.billing_portal.Session.create(customer=stripe_customer, return_url=return_url)
    url = portal.url
    if not url:
        raise RuntimeError("Stripe billing portal session did not include a URL")
    return str(url)


def update_subscription_from_event(db: Session, event: stripe.Event) -> None:
    event_type = event.get("type", "")
    data = event["data"]["object"]

    if event_type == "checkout.session.completed" and data.get("subscription"):
        _configure_stripe()
        data = stripe.Subscription.retrieve(data["subscription"])
        event_type = "customer.subscription.created"

    metadata = data.get("metadata", {}) or {}
    org_id = metadata.get("org_id") or metadata.get("orgId")
    if not org_id:
        logger.warning("Stripe event missing org_id metadata: %s", event_type)
        return

    subscription = (
        db.query(Subscription).filter(Subscription.org_id == int(org_id)).one_or_none()
    )
    if not subscription:
        subscription = Subscription(org_id=int(org_id))

    subscription.stripe_customer = data.get("customer") or subscription.stripe_customer
    subscription.stripe_subscription = data.get("id", subscription.stripe_subscription)

    plan_id = None
    if "items" in data and data["items"].get("data"):
        plan_id = data["items"]["data"][0]["price"]["id"]

    status = data.get("status")
    if status in {"trialing", "active"}:
        subscription.status = SubscriptionStatus(status)
    elif status in {"past_due", "incomplete"}:
        subscription.status = SubscriptionStatus.past_due
    else:
        subscription.status = SubscriptionStatus.canceled

    if plan_id:
        settings = get_settings()
        reverse = {
            settings.stripe_price_starter: Plan.starter,
            settings.stripe_price_pro: Plan.pro,
            settings.stripe_price_enterprise: Plan.enterprise,
        }
        subscription.plan = reverse.get(plan_id, subscription.plan)

    db.add(subscription)
    db.commit()


def sync_subscription_seats(db: Session) -> None:
    _configure_stripe()
    org_subscriptions = db.query(Subscription).filter(Subscription.status.in_([SubscriptionStatus.trialing, SubscriptionStatus.active])).all()
    for subscription in org_subscriptions:
        active_seats = (
            db.query(func.count(User.id))
            .filter(User.team.has(org_id=subscription.org_id), User.active.is_(True))
            .scalar()
        ) or 0
        subscription.seats = max(active_seats, subscription.seats or 0)
        db.add(subscription)
        if subscription.stripe_customer and subscription.plan:
            try:
                subs = stripe.Subscription.list(customer=subscription.stripe_customer, limit=1)
                if subs.data:
                    stripe.Subscription.modify(
                        subs.data[0].id,
                        items=[{"price": _price_for_plan(subscription.plan), "quantity": max(active_seats, 5)}],
                        proration_behavior="always_invoice",
                    )
            except Exception:  # pragma: no cover - network failure
                logger.exception("Failed to sync seats for org %s", subscription.org_id)
    db.commit()
