from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_reporting_service
from app.schemas.reports import IncidentResponseReport, SafetyTrendReport, ZoneHazardReport
from app.services.reporting import ReportingService

router = APIRouter(prefix="/reports", tags=["reports"])

ReportingServiceDep = Annotated[ReportingService, Depends(get_reporting_service)]


@router.get("/safety-trend", response_model=SafetyTrendReport)
async def get_safety_trend(
    service: ReportingServiceDep,
    since: Annotated[datetime | None, Query()] = None,
    until: Annotated[datetime | None, Query()] = None,
    zone_id: Annotated[UUID | None, Query()] = None,
) -> SafetyTrendReport:
    """Incidents opened/resolved and risk-level mix, bucketed by day/week/month depending on
    window length. Defaults to the trailing 30 days when since/until are omitted."""
    return await service.safety_trend(since, until, zone_id)


@router.get("/zones-hazards", response_model=ZoneHazardReport)
async def get_zone_hazard_analysis(
    service: ReportingServiceDep,
    since: Annotated[datetime | None, Query()] = None,
    until: Annotated[datetime | None, Query()] = None,
) -> ZoneHazardReport:
    """Cross-zone comparison — no zone_id filter, since this report IS the comparison."""
    return await service.zone_hazard_analysis(since, until)


@router.get("/incident-response", response_model=IncidentResponseReport)
async def get_incident_response_report(
    service: ReportingServiceDep,
    since: Annotated[datetime | None, Query()] = None,
    until: Annotated[datetime | None, Query()] = None,
    zone_id: Annotated[UUID | None, Query()] = None,
) -> IncidentResponseReport:
    return await service.incident_response(since, until, zone_id)
