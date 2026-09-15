"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration."""

    # Server
    server_name: str = "mcp-enterprise-template"
    server_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"

    # Insurance API
    insurance_api_base_url: str = "https://api.insurance-backend.example.com"
    insurance_api_key: str = "your-api-key-here"
    insurance_api_timeout: int = 30

    # Cache
    enable_caching: bool = True
    cache_ttl: int = 3600

    class Config:
        """Pydantic settings configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get application settings (cached)."""
    return Settings()
