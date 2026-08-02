from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "TaskGame"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    backend_cors_origins: str = "http://localhost:8000,http://127.0.0.1:8000"
    database_url: str = "sqlite+pysqlite:///:memory:"
    backup_dir: str = Field(default="./backups")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
