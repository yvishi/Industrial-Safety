from app.ai.config import AISettings
from app.ai.providers.base import AIProvider
from app.ai.providers.gemini import GeminiProvider


def build_ai_provider(settings: AISettings) -> AIProvider:
    """The one place that knows which concrete AIProvider to construct for
    `settings.provider` — swapping the active backend is an env var change (`AI_PROVIDER=...`),
    not a code change anywhere else in the AI layer."""
    if settings.provider == "gemini":
        return GeminiProvider(settings)
    raise ValueError(f"Unknown AI provider: {settings.provider!r}")
