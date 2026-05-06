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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
