"""
Application Configuration
=========================
Loads all configuration from environment variables / .env file using Pydantic Settings.
Provides a singleton settings instance used throughout the application.
"""

import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central application configuration loaded from environment variables."""

    # --- Application ---
    app_name: str = "AI Early Warning Business Failure Detection"
    app_env: str = "development"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000

    # --- Database ---
    database_url: str = "sqlite:///./app_data.db"

    # --- Gemini AI ---
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-pro"

    # --- File Storage ---
    upload_dir: str = "./uploads"
    reports_dir: str = "./reports"
    trained_models_dir: str = "./trained_models"

    # --- ML Model Paths ---
    model_path: str = "./trained_models/xgboost_distress_model.joblib"
    scaler_path: str = "./trained_models/feature_scaler.joblib"

    # --- CORS ---
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # --- Logging ---
    log_level: str = "INFO"

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    def ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        for dir_path in [self.upload_dir, self.reports_dir, self.trained_models_dir]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Return cached singleton Settings instance."""
    settings = Settings()
    settings.ensure_directories()
    return settings
