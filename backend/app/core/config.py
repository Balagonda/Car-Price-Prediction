"""
AutoWorth AI — Application Configuration

Uses pydantic-settings to read and validate all environment variables.
Business logic must NOT live here — this is infrastructure config only.
"""

from functools import lru_cache
from typing import Literal

from pydantic import AnyUrl, EmailStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central settings class.
    All values are read from environment variables (or .env file).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ──────────────────────────────────────────────
    # Application
    # ──────────────────────────────────────────────
    APP_NAME: str = "AutoWorth AI"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True
    FRONTEND_URL: str = "http://localhost:3000"

    # ──────────────────────────────────────────────
    # Database
    # ──────────────────────────────────────────────
    DATABASE_URL: str

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v.startswith("postgresql+asyncpg://"):
            raise ValueError(
                "DATABASE_URL must use the 'postgresql+asyncpg://' scheme. "
                "SQLite and other drivers are not supported."
            )
        return v

    # ──────────────────────────────────────────────
    # JWT Authentication
    # ──────────────────────────────────────────────
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long.")
        return v

    # ──────────────────────────────────────────────
    # Google OAuth
    # ──────────────────────────────────────────────
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # ──────────────────────────────────────────────
    # Cloudinary
    # ──────────────────────────────────────────────
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    # ──────────────────────────────────────────────
    # Email (SMTP)
    # ──────────────────────────────────────────────
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM_NAME: str = "AutoWorth AI"

    # ──────────────────────────────────────────────
    # ML Storage
    # ──────────────────────────────────────────────
    MODEL_ARTIFACTS_DIR: str = "./app/ml/artifacts"
    MAX_UPLOAD_SIZE_MB: int = 10

    # ──────────────────────────────────────────────
    # Computer Vision (Phase 4)
    # ──────────────────────────────────────────────
    CV_TIMEOUT_SECONDS: int = 5
    # Path to YOLO weights file. If the file is absent, YOLOv8n is auto-downloaded.
    YOLO_MODEL_PATH: str = "./app/ml/artifacts/yolov8n.pt"
    # Root folder prefix inside Cloudinary (no trailing slash)
    CLOUDINARY_FOLDER_PREFIX: str = "autoworth"

    # ──────────────────────────────────────────────
    # Derived helpers
    # ──────────────────────────────────────────────
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def cors_origins(self) -> list[str]:
        """Allowed CORS origins based on environment."""
        if self.is_production:
            return [self.FRONTEND_URL]
        return [
            self.FRONTEND_URL,
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]


@lru_cache
def get_settings() -> Settings:
    """
    Return the cached Settings singleton.
    Use this as a FastAPI dependency: Depends(get_settings)
    """
    return Settings()
