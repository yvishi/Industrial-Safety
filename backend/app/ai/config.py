from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class AISettings(BaseSettings):
    """
    Configuration for the AI Foundation layer — provider credentials/model and generation
    defaults. Kept as its own settings class (rather than folded into app.core.config.Settings)
    so the AI module stays a self-contained, independently configurable unit, with its own
    `AI_`-prefixed env vars that can't collide with the rest of the app's config.

    Every field has a safe default and none are required: the app must boot and run with no AI
    configuration at all (`configured` on GeminiProvider is False, requests to generate() raise
    AIProviderNotConfiguredError) — the AI layer is additive, never a hard dependency of the
    platform.
    """

    # extra="ignore": this shares the app's single .env file (see app.core.config.Settings),
    # which has plenty of keys outside the AI_ prefix — env_prefix only changes which var name
    # each field reads from, it doesn't filter unrelated keys out of the file, so without this
    # pydantic-settings treats every other key in .env as an invalid extra field.
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", env_prefix="AI_", extra="ignore"
    )

    # Which AIProvider implementation to construct — see app.ai.providers.factory.
    provider: str = "gemini"

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"

    # Generation defaults — every AIProvider.generate() call falls back to these unless a
    # caller overrides them explicitly, e.g. a future capability that wants a more
    # deterministic temperature than another.
    temperature: float = 0.3
    max_output_tokens: int = 1024


@lru_cache
def get_ai_settings() -> AISettings:
    return AISettings()
