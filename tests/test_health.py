import os
import sys
from pathlib import Path

# Ensure project root on path and required env vars before importing the app.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DB_PATH = ROOT / "test_app.db"

os.environ.setdefault("DATABASE_URL", f"sqlite:///{DB_PATH}")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("RMHT_ADMIN_TOKEN", "test-admin")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def test_healthcheck_returns_ok() -> None:
    """The /healthz endpoint should respond with a JSON ok payload."""
    if DB_PATH.exists():
        DB_PATH.unlink()

    with TestClient(app) as client:
        response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    if DB_PATH.exists():
        DB_PATH.unlink()
