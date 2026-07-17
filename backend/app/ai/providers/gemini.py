from google import genai
from google.genai import types

from app.ai.config import AISettings
from app.ai.exceptions import AIProviderNotConfiguredError
from app.ai.providers.base import AIGenerationResult, AIProvider


class GeminiProvider(AIProvider):
    """Google Gemini implementation of AIProvider — the only concrete provider in v1.

    The client is constructed once at instantiation (None if no API key is configured, so a
    missing key fails fast and clearly on the first generate() call rather than surfacing as an
    opaque SDK error). Every other part of the AI layer depends on AIProvider, not this class.
    """

    def __init__(self, settings: AISettings) -> None:
        self._settings = settings
        self._client = genai.Client(api_key=settings.gemini_api_key) if settings.gemini_api_key else None

    @property
    def is_configured(self) -> bool:
        return self._client is not None

    async def generate(
        self,
        *,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
    ) -> AIGenerationResult:
        if self._client is None:
            raise AIProviderNotConfiguredError(
                "Gemini provider has no API key configured (set AI_GEMINI_API_KEY)"
            )

        response = await self._client.aio.models.generate_content(
            model=self._settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature if temperature is not None else self._settings.temperature,
                max_output_tokens=(
                    max_output_tokens if max_output_tokens is not None else self._settings.max_output_tokens
                ),
            ),
        )
        return AIGenerationResult(
            text=response.text or "",
            model=self._settings.gemini_model,
            provider="gemini",
        )
