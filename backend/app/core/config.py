from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Industrial Safety Intelligence Platform API"
    environment: str = "development"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/industrial_safety"

    # Origins allowed to call the API. The Vite dev server runs on 5173 by default.
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Plant simulation engine (runs inside the API process when enabled;
    # see app/simulation/runner.py for the standalone-process alternative).
    simulation_enabled: bool = True
    simulation_tick_seconds: float = 5.0
    sensor_reading_retention_hours: int = 24


@lru_cache
def get_settings() -> Settings:
    return Settings()
