"""Application configuration using Pydantic settings."""
from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from pydantic import AnyHttpUrl, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _canonical_env(value: str) -> str:
    mapping = {
        "prod": "production",
        "production": "production",
        "development": "development",
        "dev": "development",
        "testing": "test",
        "test": "test",
    }
    return mapping.get(value.lower(), value.lower())


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    app_env: str = Field("development", alias="APP_ENV")
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")
    secret_key: str = Field("dev-insecure-key", alias="SECRET_KEY")
    rmht_admin_token: str = Field("changeme", alias="RMHT_ADMIN_TOKEN")
    cors_allow_origins: str = Field("*", alias="CORS_ALLOW_ORIGINS")
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

    @field_validator("app_env", mode="before")
    @classmethod
    def normalize_env(cls, value: str) -> str:
        """Normalize environment aliases to canonical names."""
        return _canonical_env(value) if isinstance(value, str) else value

    @model_validator(mode="after")
    def validate_configuration(self) -> "Settings":
        """Normalize CORS entries and enforce production requirements."""
        env = self.app_env
        parsed = self._parse_cors(self.cors_allow_origins)

        if env == "production":
            if self.secret_key in ("dev-insecure-key", ""):
                raise ValueError("SECRET_KEY must be set to a strong value in production")
            if self.rmht_admin_token in ("changeme", ""):
                raise ValueError("RMHT_ADMIN_TOKEN must be set to a strong value in production")
            if not parsed or "*" in parsed:
                raise ValueError("CORS_ALLOW_ORIGINS must be explicitly set (no wildcards) in production")
            object.__setattr__(self, "_allowed_cors_cache", parsed)
        else:
            dev_defaults = ["http://localhost:5173", "http://127.0.0.1:5173"]
            if not parsed or "*" in parsed:
                parsed = dev_defaults.copy()
            else:
                for origin in dev_defaults:
                    if origin not in parsed:
                        parsed.append(origin)
            object.__setattr__(self, "_allowed_cors_cache", parsed)

        return self

    @staticmethod
    def _parse_cors(value: str) -> List[str]:
        if not value:
            return []
        return [origin.strip() for origin in value.split(",") if origin.strip()]

    @property
    def allowed_cors_origins(self) -> List[str]:
        return getattr(self, "_allowed_cors_cache", [])

    @property
    def admin_token(self) -> str:
        """Backward compatible alias for the admin token."""
        return self.rmht_admin_token

    @property
    def resolved_database_url(self) -> str:
        """Return the configured database URL or a dev-friendly fallback."""
        if self.database_url:
            return self.database_url
        if self.app_env != "production":
            return "sqlite:///./rmht.db"
        raise ValueError("DATABASE_URL is required in production")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()  # type: ignore[call-arg]
