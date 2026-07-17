from app.core.exceptions import AppError


class AIProviderNotConfiguredError(AppError):
    """Raised when a provider is asked to generate() without the credentials it needs (e.g. no
    API key configured) — a 503, since the AI layer is temporarily unavailable rather than the
    request itself being invalid."""

    status_code = 503


class AITemplateNotFoundError(AppError):
    """Raised when a caller asks AIService.generate() for a template_id that isn't registered
    in app.ai.prompts.templates."""

    status_code = 400
