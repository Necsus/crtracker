"""Application configuration using Pydantic Settings."""

from functools import lru_cache

from pydantic import Field, PositiveInt
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="CRTracker API", description="Application name")
    app_version: str = Field(default="1.0.0", description="API version")
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(
        description="Environment (development, staging, production)",
    )

    # Database
    database_url: str = Field(
        description="PostgreSQL database URL (async)",
    )
    database_echo: bool = Field(default=False, description="Echo SQL queries")

    # Security
    secret_key: str = Field(
        description="Secret key for JWT encoding",
    )
    access_token_expire_minutes: PositiveInt = Field(
        default=60 * 24 * 7,  # 7 days
        description="Access token expiration in minutes",
    )

    # LLM Providers (Oracle Service)
    openai_api_key: str = Field(default="", description="OpenAI API key")
    groq_api_key: str = Field(default="", description="Groq API key")
    llm_provider: str = Field(
        default="groq",
        description="LLM provider to use (openai, groq)",
    )
    llm_model: str = Field(
        default="llama-3.3-70b-versatile",
        description="LLM model identifier",
    )

    # CORS
    allowed_origins: list[str] = Field(
        description="Allowed CORS origins",
    )

    # Pagination
    default_page_size: PositiveInt = Field(
        default=20,
        description="Default page size for pagination",
    )
    max_page_size: PositiveInt = Field(
        default=100,
        description="Maximum page size for pagination",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
