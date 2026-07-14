from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_recommendation_service
from app.schemas.common import Page
from app.schemas.recommendation import (
    PlantRecommendationSummary,
    RecommendationRead,
    RecommendationTemplateEntry,
)
from app.services.recommendation import RecommendationService, build_template_catalog

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

RecommendationServiceDep = Annotated[RecommendationService, Depends(get_recommendation_service)]


@router.get("/zones/{zone_id}", response_model=list[RecommendationRead])
async def get_zone_recommendations(
    zone_id: UUID,
    service: RecommendationServiceDep,
    include_resolved: Annotated[bool, Query()] = False,
) -> list[RecommendationRead]:
    """Active recommendations for a zone, priority-sorted — always live, same "no caching"
    philosophy as /risk/zones/{id}."""
    return await service.get_zone_recommendations(zone_id, include_resolved=include_resolved)


@router.get("/plant", response_model=PlantRecommendationSummary)
async def get_plant_recommendations(service: RecommendationServiceDep) -> PlantRecommendationSummary:
    """Cross-zone Action Queue — the top priority-ranked recommendations plant-wide."""
    return await service.get_plant_summary()


@router.get("/zones/{zone_id}/history", response_model=Page[RecommendationRead])
async def get_zone_recommendation_history(
    zone_id: UUID,
    service: RecommendationServiceDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> Page[RecommendationRead]:
    items, total = await service.history_for_zone(zone_id, page=page, page_size=page_size)
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.post("/{recommendation_id}/acknowledge", response_model=RecommendationRead)
async def acknowledge_recommendation(
    recommendation_id: UUID, service: RecommendationServiceDep
) -> RecommendationRead:
    return await service.acknowledge(recommendation_id)


@router.post("/{recommendation_id}/resolve", response_model=RecommendationRead)
async def resolve_recommendation(recommendation_id: UUID, service: RecommendationServiceDep) -> RecommendationRead:
    return await service.resolve(recommendation_id)


@router.get("/templates", response_model=list[RecommendationTemplateEntry])
async def get_recommendation_templates() -> list[RecommendationTemplateEntry]:
    """Static template catalog introspected from config — no DB — for auditability of what the
    engine can recommend."""
    return build_template_catalog()
