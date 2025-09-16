"""Shared FastAPI dependencies."""
from __future__ import annotations

from typing import Iterator

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.session import SessionLocal


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_session(request: Request) -> dict:
    session = request.session or {}
    if "user_id" not in session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return session


def require_role(*roles: str):
    def checker(session: dict = Depends(require_session)) -> dict:
        if session.get("role") not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return session

    return checker


def require_csrf(request: Request) -> None:
    token = request.headers.get("X-CSRF-Token") or request.headers.get("X-CSRF-TOKEN")
    session_token = (request.session or {}).get("csrf_token")
    if not session_token or token != session_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF validation failed")
