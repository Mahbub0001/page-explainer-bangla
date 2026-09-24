from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    GOOGLE_API_KEY: str = ""
    GEMINI_CHAT_MODEL: str = "gemini-2.5-flash"
    GEMINI_EMBEDDING_MODEL: str = "models/gemini-embedding-001"
    EMBEDDING_DIMENSIONS: int = 768
    LLM_TEMPERATURE: float = 0.3

    APP_ENV: str = "dev"
    LOG_LEVEL: str = "INFO"
    CORS_ALLOW_ORIGIN_REGEX: str = r"^chrome-extension://.*$"
    CORS_EXTRA_ORIGINS: str = ""

    MAX_TEXT_CHARS: int = 120000
    MIN_TEXT_CHARS: int = 100
    CHUNK_SIZE: int = 1500
    CHUNK_OVERLAP: int = 150
    MAX_CHUNKS: int = 50
    RETRIEVAL_K: int = 5
    STUFF_LIMIT_CHARS: int = 60000
    MAP_CHUNK_CHARS: int = 8000
    MAP_CONCURRENCY: int = 3
    CACHE_MAX_PAGES: int = 30
    CACHE_TTL_SECONDS: int = 7200
    RATE_LIMIT_PER_MINUTE: int = 40
    REQUEST_TIMEOUT_SECONDS: int = 90

    @property
    def is_llm_configured(self) -> bool:
        key = self.GOOGLE_API_KEY.strip()
        return bool(key and key != "your-gemini-api-key-here")

    @property
    def cors_origins(self) -> List[str]:
        if not self.CORS_EXTRA_ORIGINS:
            return []
        return [origin.strip() for origin in self.CORS_EXTRA_ORIGINS.split(",") if origin.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
