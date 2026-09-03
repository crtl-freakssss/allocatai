from functools import lru_cache
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application Information
    app_name: str = Field(default="AllocateAI Backend", description="Application display name")
    app_version: str = Field(default="0.1.0", description="Application semantic version")
    environment: str = Field(
        default="development",
        description="Runtime environment (development, staging, production, test)",
    )
    debug: bool = Field(default=False, description="Debug mode flag")

    # API Routing & Versioning
    api_prefix: str = Field(default="/api", description="Base API prefix")
    api_v1_prefix: str = Field(default="/api/v1", description="API version 1 prefix")
    schema_version: str = Field(default="v1", description="Default API schema version")

    # CORS
    cors_origins: Union[List[str], str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins as list or comma-separated string",
    )

    # Database
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/allocateai",
        description="SQLAlchemy-compatible PostgreSQL connection URL",
    )
    db_pool_size: int = Field(default=5, description="Connection pool size")
    db_max_overflow: int = Field(default=10, description="Max overflow connections")
    db_pool_timeout: int = Field(default=30, description="Connection pool timeout in seconds")
    db_echo: bool = Field(default=False, description="Echo SQL statements to stdout")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            # Parse comma-separated string or handle single origin
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, list):
            return [str(item).strip() for item in v if str(item).strip()]
        return []

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def cors_origin_list(self) -> List[str]:
        if isinstance(self.cors_origins, list):
            return self.cors_origins
        return [self.cors_origins]


@lru_cache()
def get_settings() -> Settings:
    """Return a cached instance of application settings."""
    return Settings()
