from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "table_project"
    environment: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:15432/table_project"
    test_database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:15432/table_project_test"
    )
    redis_url: str = "redis://localhost:6380/0"
    clerk_publishable_key: str = ""
    clerk_secret_key: str = ""
    clerk_jwks_url: str = ""
    clerk_webhook_secret: str = ""
    data_export_storage_path: Path = Path(__file__).resolve().parents[3] / "data" / "exports"
    data_export_ttl_days: int = 7

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-haiku-4-5"
    google_api_key: str = ""
    google_model: str = "gemini-2.5-flash"
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-v4-flash"

    redis_enrichment_ttl_days: int = 30
    redis_preview_ttl_seconds: int = 3600
    daily_cost_cap_usd: float = 0.02

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
