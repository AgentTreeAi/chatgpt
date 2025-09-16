"""Authentication routes for passwordless magic links."""
from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import create_token, decode_token, generate_csrf_token
from app.db import models
from app.dependencies import get_db
from app.services.email import send_magic_link

router = APIRouter(prefix="/auth", tags=["auth"])


class MagicLinkRequest(BaseModel):
    email: EmailStr


@router.post("/request-link", status_code=status.HTTP_202_ACCEPTED)
def request_magic_link(
    payload: MagicLinkRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    email = payload.email.lower()
    domain = email.split("@")[-1]

    org = db.query(models.Org).filter(models.Org.allowed_domains.contains([domain])).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No organization for domain")

    user = db.query(models.User).filter(func.lower(models.User.email) == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    nonce_value = create_token({"email": email}, expires_delta=timedelta(minutes=5))
    expires_at = datetime.utcnow() + timedelta(minutes=5)

    nonce = models.EmailLoginNonce(org_id=org.id, email=email, token=nonce_value, expires_at=expires_at)
    db.add(nonce)
    db.commit()

    callback_url = str(request.url_for("auth_callback"))
    link = f"{callback_url}?token={nonce_value}"
    send_magic_link(email, link)

    return {"detail": "Magic link sent"}


@router.get("/callback")
def auth_callback(
    token: str,
    request: Request,
    db: Session = Depends(get_db),
) -> Response:
    try:
        payload = decode_token(token)
    except ValueError as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token") from exc

    email = payload.get("email")
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token payload")

    nonce = (
        db.query(models.EmailLoginNonce)
        .filter(models.EmailLoginNonce.token == token, models.EmailLoginNonce.used.is_(False))
        .first()
    )
    if not nonce:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Magic link expired")

    if nonce.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Magic link expired")

    user = db.query(models.User).join(models.Team).filter(func.lower(models.User.email) == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    nonce.used = True
    db.commit()

    request.session.clear()
    request.session.update(
        {
            "user_id": user.id,
            "org_id": user.team.org_id,
            "team_id": user.team_id,
            "role": user.role,
            "csrf_token": generate_csrf_token(),
        }
    )

    response = RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)
    response.set_cookie("csrftoken", request.session["csrf_token"], httponly=False, samesite="lax")
    return response


@router.post("/logout")
def logout(request: Request) -> dict[str, str]:
    request.session.clear()
    return {"detail": "Logged out"}
