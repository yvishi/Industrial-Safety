from pydantic import BaseModel


class AIHealthResponse(BaseModel):
    """GET /api/v1/ai/health — reports which provider is active and whether it's actually
    usable (has credentials), without making a generation call."""

    provider: str
    model: str
    configured: bool


class AIGenerateRequest(BaseModel):
    template_id: str = "incident_explanation"
    question: str | None = None


class AIGenerateResponse(BaseModel):
    text: str
    model: str
    provider: str
    template_id: str
