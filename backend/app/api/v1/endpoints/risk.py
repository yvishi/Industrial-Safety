from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_risk_service
from app.risk_engine.config.defaults import DEFAULT_RISK_CONFIG
from app.schemas.common import Page
from app.schemas.risk import PlantRiskSummary, RiskAssessment, RiskSnapshotRead, RuleCatalogEntry
from app.services.risk import RiskService, build_rule_catalog

router = APIRouter(prefix="/risk", tags=["risk"])

RiskServiceDep = Annotated[RiskService, Depends(get_risk_service)]


@router.get("/zones/{zone_id}", response_model=RiskAssessment)
async def get_zone_risk(zone_id: UUID, service: RiskServiceDep) -> RiskAssessment:
    """Live-computed assessment — always fresh, same "no caching" philosophy as /state."""
    return await service.assess_zone(zone_id)


@router.get("/plant", response_model=PlantRiskSummary)
async def get_plant_risk(service: RiskServiceDep) -> PlantRiskSummary:
    return await service.assess_plant()


@router.get("/zones/{zone_id}/history", response_model=Page[RiskSnapshotRead])
async def get_zone_risk_history(
    zone_id: UUID,
    service: RiskServiceDep,
    since: Annotated[datetime | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> Page[RiskSnapshotRead]:
    items, total = await service.history_for_zone(zone_id, since=since, page=page, page_size=page_size)
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.get("/changes", response_model=list[RiskSnapshotRead])
async def get_recent_risk_changes(
    service: RiskServiceDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[RiskSnapshotRead]:
    """Every persisted snapshot is, by construction, a meaningful level/score change — so this
    is simply the most recent rows, newest first, with no separate diff query needed."""
    return await service.recent_level_changes(limit=limit)


@router.get("/rules", response_model=list[RuleCatalogEntry])
async def get_rule_catalog() -> list[RuleCatalogEntry]:
    """Static rule catalog introspected from config — no DB — for auditability of what the
    engine can detect."""
    return build_rule_catalog(DEFAULT_RISK_CONFIG)
