"""Route modules for FastAPI app."""
from . import admin, auth, billing_stripe, health, integrations_slack, jobs, public, spa_api

__all__ = [
    "admin",
    "auth",
    "billing_stripe",
    "health",
    "integrations_slack",
    "jobs",
    "public",
    "spa_api",
]
