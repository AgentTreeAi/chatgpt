"""Security utilities for passwordless auth and signing tokens."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import secrets

from jose import JWTError, jwt

from .config import get_settings


ALGORITHM = "HS256"


def create_token(data: Dict[str, Any], expires_delta: timedelta) -> str:
    """Create a signed JWT with expiration."""

    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    settings = get_settings()
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """Decode a JWT and return payload."""

    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid token") from exc
    return payload


def generate_csrf_token() -> str:
    """Generate a random CSRF token."""

    return secrets.token_urlsafe(32)
