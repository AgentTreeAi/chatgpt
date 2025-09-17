"""Stripe billing routes."""
from __future__ import annotations


import stripe

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import models
from app.db.models import Plan
from app.dependencies import get_db, require_csrf, require_role
from app.services import billing as billing_service

router = APIRouter(prefix="/billing", tags=["billing"])


class CheckoutRequest(BaseModel):
    plan: Plan
    seats: int = Field(default=5, ge=1)


class PortalRequest(BaseModel):
    return_url: str


def _create_checkout_session(
    db: Session,
    session: dict,
    request: Request,
    plan: Plan,
    seats: int,
) -> str:
    settings = get_settings()
    base_url = settings.app_base_url or str(request.base_url).rstrip("/")
    success_url = f"{base_url}/admin"
    cancel_url = f"{base_url}/admin"

    try:
        checkout_url = billing_service.create_checkout_session(
            org_id=session["org_id"],
            plan=plan,
            quantity=max(seats, 1),
            success_url=success_url,
            cancel_url=cancel_url,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    subscription = (
        db.query(models.Subscription)
        .filter(models.Subscription.org_id == session["org_id"])
        .one_or_none()
    )
    if not subscription:
        subscription = models.Subscription(org_id=session["org_id"], plan=plan)
    subscription.plan = plan
    subscription.status = models.SubscriptionStatus.trialing
    db.add(subscription)
    db.commit()

    return checkout_url


@router.post("/checkout")
def create_checkout(
    payload: CheckoutRequest,
    request: Request,
    session: dict = Depends(require_role("org_admin")),
    db: Session = Depends(get_db),
    _: None = Depends(require_csrf),
) -> dict[str, str]:
    checkout_url = _create_checkout_session(db, session, request, payload.plan, payload.seats)

    return {"checkout_url": checkout_url}


@router.get("/checkout")
def checkout_redirect(
    request: Request,
    plan: str = "starter",
    seats: int = 5,
    session: dict = Depends(require_role("org_admin")),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    try:
        plan_enum = Plan(plan.lower())
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid plan") from exc

    checkout_url = _create_checkout_session(db, session, request, plan_enum, seats)
    return RedirectResponse(url=checkout_url, status_code=status.HTTP_303_SEE_OTHER)


@router.post("/portal")
def create_portal(
    payload: PortalRequest,
    session: dict = Depends(require_role("org_admin")),
    db: Session = Depends(get_db),
    _: None = Depends(require_csrf),
) -> dict[str, str]:
    subscription = (
        db.query(models.Subscription)
        .filter(models.Subscription.org_id == session["org_id"])
        .one_or_none()
    )
    if not subscription or not subscription.stripe_customer:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No Stripe customer found")

    try:
        url = billing_service.create_billing_portal(subscription.stripe_customer, payload.return_url)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return {"portal_url": url}


@router.post("/webhooks/stripe", status_code=status.HTTP_200_OK)
async def stripe_webhook(request: Request, db: Session = Depends(get_db)) -> dict[str, str]:
    settings = get_settings()
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Webhook secret not configured")

    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")
    if not sig_header:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing signature header")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=settings.stripe_webhook_secret,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature") from exc

    billing_service.update_subscription_from_event(db, event)
    return {"status": "processed"}
