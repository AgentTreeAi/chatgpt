"""Application configuration using Pydantic settings."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Literal

from pydantic import AnyHttpUrl, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    app_env: Literal["dev", "prod", "test"] = Field("dev", alias="APP_ENV")
    database_url: Optional[str] = Field(None, alias="DATABASE_URL")
    secret_key: str = Field("dev-secret-key-change-in-production", alias="SECRET_KEY")
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
    allowed_cors_origins: List[str] = Field(default_factory=list, alias="ALLOWED_CORS_ORIGINS")
    sqlite_database_path: Path = Field(Path("rmht.db"), alias="SQLITE_DATABASE_PATH")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    @field_validator("allowed_cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from CSV string or use default."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, list):
            return v
        else:
            return ["*"]  # Default for dev

    @model_validator(mode="after")
    def validate_production_config(self):
        """Validate production configuration requirements."""
        if self.app_env == "prod":
            if not self.database_url:
                raise ValueError("DATABASE_URL must be set in production")

            # Require strong secrets in production
            if self.secret_key in ("dev-secret-key-change-in-production", ""):
                raise ValueError("SECRET_KEY must be set to a strong value in production")
            if self.admin_token in ("changeme", ""):
                raise ValueError("RMHT_ADMIN_TOKEN must be set to a strong value in production")
            
            # Require explicit CORS origins in production
            if not self.allowed_cors_origins or "*" in self.allowed_cors_origins:
                raise ValueError("ALLOWED_CORS_ORIGINS must be explicitly set (no wildcards) in production")
        
        # Set default CORS for dev environments
        if self.app_env != "prod" and not self.allowed_cors_origins:
            self.allowed_cors_origins = ["*"]
        
        return self

    @property
    def resolved_database_url(self) -> str:
        """Return the database URL with sensible development defaults."""

        if self.database_url:
            return self.database_url

        if self.app_env == "prod":
            raise ValueError("DATABASE_URL must be set in production")

        sqlite_path = self.sqlite_database_path
        if not sqlite_path.is_absolute():
            sqlite_path = Path.cwd() / sqlite_path

        return f"sqlite:///{sqlite_path}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()
