from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class AIGenerationResult:
    """The one return shape every AIProvider produces, regardless of backend — callers (AIService,
    the API layer) never see provider-specific response objects."""

    text: str
    model: str
    provider: str


class AIProvider(ABC):
    """
    The seam the rest of the AI layer codes against. AIService, the Context Builder, and the
    prompt templates never import a concrete provider (e.g. GeminiProvider) directly — only
    app.ai.providers.factory.build_ai_provider does, based on configuration. Swapping Gemini for
    another backend, or adding a second provider alongside it, means implementing this one
    interface; nothing in context/, prompts/, or service.py changes.
    """

    @abstractmethod
    async def generate(
        self,
        *,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
    ) -> AIGenerationResult:
        """Generate a single completion for `prompt` (optionally guided by `system_prompt`).

        `temperature`/`max_output_tokens` override the provider's configured defaults for this
        call only — most callers omit them and get the configured defaults; a future capability
        that needs a different setting (e.g. a more deterministic analytics Q&A) can override
        per call without touching configuration.
        """
        raise NotImplementedError
