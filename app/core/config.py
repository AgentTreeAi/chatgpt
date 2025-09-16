"""Application configuration using Pydantic settings."""
from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    database_url: str = Field(..., alias="DATABASE_URL")
    secret_key: str = Field(..., alias="SECRET_KEY")
    admin_token: str = Field("changeme", alias="RMHT_ADMIN_TOKEN")
    sendgrid_api_key: Optional[str] = Field(None, alias="SENDGRID_API_KEY")
    slack_client_id: Optional[str] = Field(None, alias="SLACK_CLIENT_ID")
    slack_client_secret: Optional[str] = Field(None, alias="SLACK_CLIENT_SECRET")
    stripe_secret_key: Optional[str] = Field(None, alias="STRIPE_SECRET_KEY")
    stripe_webhook_secret: Optional[str] = Field(None, alias="STRIPE_WEBHOOK_SECRET")
    stripe_price_starter: Optional[str] = Field(None, alias="STRIPE_PRICE_STARTER")
    stripe_price_pro: Optional[str] = Field(None, alias="STRIPE_PRICE_PRO")
    stripe_price_enterprise: Optional[str] = Field(None, alias="STRIPE_PRICE_ENTERPRISE")
    app_base_url: Optional[AnyHttpUrl] = Field(None, alias="APP_BASE_URL")
    cron_secret: Optional[str] = Field(None, alias="CRON_SECRET")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    allowed_cors_origins: List[AnyHttpUrl] = Field(default_factory=list)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()
