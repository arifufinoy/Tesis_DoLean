from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DoLean Backend"
    app_version: str = "0.1.0"
    environment: str = "development"
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://dolean:change-me-local@db:5432/dolean"
    redis_url: str = "redis://redis:6379/0"
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "change-me-minio"
    minio_secure: bool = False
    minio_bucket: str = "audio-files"
    cors_origins: str = Field(default="http://localhost:3000,http://localhost:5173")
    jwt_secret_key: str = "change-me-local-jwt-secret-at-least-32-characters"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    password_reset_expire_minutes: int = 30
    smtp_host: str = "mailpit"
    smtp_port: int = 1025
    smtp_from_email: str = "no-reply@dolean.local"
    password_reset_url: str = "http://localhost:3000/reset-password"
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

