from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./data/inkguard.db"
    JWT_SECRET: str = "inkguard-insecure-dev-secret-change-in-production-1234567890"
    DEMO_MODE: bool = False
    DEMO_PASSWORD: str = "LumoDemo2026!"
    LLM_MODE: str = "mock"  # live, cached, mock, rules_only
    LLM_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    GOOGLE_API_KEY: str = ""
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gemini-3.5-flash-lite"
    LLM_DAILY_CAP: int = 100
    MAX_CONTENT_CHARS: int = 20000
    RATE_LIMIT_REVIEWS_PER_HOUR: int = 60
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    ALLOW_SEED_RESET: bool = True
    NEXT_PUBLIC_API_BASE: str = "http://localhost:8000/api/v1"
    VERIFIER_ENABLED: bool = False

    @property
    def effective_api_key(self) -> str:
        import os
        return self.LLM_API_KEY or self.GOOGLE_API_KEY or os.environ.get("GOOGLE_API_KEY", "") or os.environ.get("LLM_API_KEY", "")

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
