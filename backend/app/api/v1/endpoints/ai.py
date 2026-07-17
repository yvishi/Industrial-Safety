from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.ai.config import AISettings, get_ai_settings
from app.ai.context.builder import ContextBuilder
from app.ai.context.schemas import AIContext
from app.ai.service import AIService
from app.api.deps import get_ai_context_builder, get_ai_service
from app.schemas.ai import AIGenerateRequest, AIGenerateResponse, AIHealthResponse

router = APIRouter(prefix="/ai", tags=["ai"])

ContextBuilderDep = Annotated[ContextBuilder, Depends(get_ai_context_builder)]
AIServiceDep = Annotated[AIService, Depends(get_ai_service)]


@router.get("/health", response_model=AIHealthResponse)
async def get_ai_health(settings: Annotated[AISettings, Depends(get_ai_settings)]) -> AIHealthResponse:
    """Reports which provider/model is configured and whether it actually has credentials —
    no generation call, safe to poll from ops tooling or a future settings page."""
    return AIHealthResponse(
        provider=settings.provider,
        model=settings.gemini_model,
        configured=bool(settings.gemini_api_key),
    )


@router.get("/context/incidents/{incident_id}", response_model=AIContext)
async def get_incident_context(incident_id: UUID, builder: ContextBuilderDep) -> AIContext:
    """Foundation demo: exercises the Context Builder for "why did this incident happen"
    without calling the LLM — lets context assembly be verified independently of the provider."""
    return await builder.build_incident_context(incident_id)


@router.post("/incidents/{incident_id}/generate", response_model=AIGenerateResponse)
async def generate_incident_response(
    incident_id: UUID,
    payload: AIGenerateRequest,
    builder: ContextBuilderDep,
    service: AIServiceDep,
) -> AIGenerateResponse:
    """Foundation demo: the full pipeline (Context Builder -> prompt template -> provider) for
    the incident scope. Proves the AI layer end to end without being a shipped capability — no
    conversation history, no streaming, a single request/response."""
    context = await builder.build_incident_context(incident_id)
    result = await service.generate(
        template_id=payload.template_id,
        context=context,
        **({"question": payload.question} if payload.question else {}),
    )
    return AIGenerateResponse(
        text=result.text,
        model=result.model,
        provider=result.provider,
        template_id=payload.template_id,
    )
