"""Configuration behaviour smoke tests."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_dev_uses_sqlite_fallback(monkeypatch, tmp_path):
    """Development mode should fall back to SQLite when DATABASE_URL is absent."""

    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("APP_ENV", "dev")
    sqlite_path = tmp_path / "dev.db"
    monkeypatch.setenv("SQLITE_DATABASE_PATH", str(sqlite_path))

    settings = Settings()

    expected_url = f"sqlite:///{sqlite_path}"
    assert settings.resolved_database_url == expected_url
    assert settings.sqlite_database_path == Path(str(sqlite_path))


def test_prod_requires_database_url(monkeypatch):
    """Production must fail fast when DATABASE_URL is missing."""

    monkeypatch.setenv("APP_ENV", "prod")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("SECRET_KEY", "super-secret-key")
    monkeypatch.setenv("RMHT_ADMIN_TOKEN", "super-admin-token")
    monkeypatch.setenv("ALLOWED_CORS_ORIGINS", "[\"https://example.com\"]")

    with pytest.raises(ValidationError):
        Settings()
