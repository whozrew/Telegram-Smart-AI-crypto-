"""
Core configuration using pydantic-settings.
Loads from .env file automatically.
"""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Telegram
    BOT_TOKEN: str

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Gemini
    GEMINI_API_KEY: str

    # Admins
    ADMIN_IDS: str = ""

    # User Limits
    MAX_ACTIVE_USERS: int = 1000

    # Cache TTL (seconds)
    CACHE_TTL: int = 3600
    SEARCH_CACHE_TTL: int = 1800
    PRICE_CACHE_TTL: int = 900

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/bot.log"

    # Rate limiting
    RATE_LIMIT_MESSAGES: int = 5
    RATE_LIMIT_PERIOD: int = 60
    SEARCH_COOLDOWN: int = 3

    # Scraping
    PLAYWRIGHT_HEADLESS: bool = True
    SCRAPE_TIMEOUT: int = 30
    MAX_RETRIES: int = 3

    # Pagination
    RESULTS_PER_PAGE: int = 5
    MAX_RESULTS: int = 50

    # Alerts
    PRICE_CHECK_INTERVAL: int = 3600
    ALERT_BATCH_SIZE: int = 100

    # App
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    @property
    def admin_ids_list(self) -> List[int]:
        if not self.ADMIN_IDS:
            return []
        return [int(x.strip()) for x in self.ADMIN_IDS.split(",") if x.strip().isdigit()]

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_db_url(cls, v: str) -> str:
        # Railway sometimes provides postgres:// instead of postgresql+asyncpg://
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgresql://") and "+asyncpg" not in v:
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
