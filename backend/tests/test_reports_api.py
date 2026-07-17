from datetime import datetime, timezone
from uuid import UUID

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.incident import IncidentRepository
from app.repositories.recommendation import RecommendationRepository
from app.repositories.risk import RiskRepository
from app.risk_engine.rules import ALL_RULES


async def _create_plant_and_zone(client: AsyncClient, zone_code: str = "ZN-01") -> tuple[str, str]:
    plant = (await client.post("/api/v1/plants", json={"code": "TST-01", "name": "Test Plant"})).json()
    zone = (
        await client.post(
            "/api/v1/zones",
            json={
                "plant_id": plant["id"],
                "code": zone_code,
                "name": "Crude Distillation Unit",
                "zone_type": "crude_distillation",
            },
        )
    ).json()
    return plant["id"], zone["id"]


async def _create_incident(
    db_session: AsyncSession,
    *,
    zone_id: str,
    opened_at: datetime,
    resolved_at: datetime | None = None,
    closed_at: datetime | None = None,
    status: str = "open",
    classification: str = "operational_episode",
) -> None:
    await IncidentRepository(db_session).create(
        {
            "primary_zone_id": UUID(zone_id),
            "affected_zone_ids": [zone_id],
            "status": status,
            "origin": "system_detected",
            "classification": classification,
            "risk_severity_at_open": "high",
            "peak_risk_severity": "high",
            "title": "Test incident",
            "summary": "Seeded for reporting tests",
            "opened_at": opened_at,
            "resolved_at": resolved_at,
            "closed_at": closed_at,
            "root_cause": None,
            "corrective_actions": [],
        }
    )


async def _create_snapshot(
    db_session: AsyncSession,
    *,
    zone_id: str,
    evaluated_at: datetime,
    level: str = "normal",
    score: int = 0,
    contributors: list[dict] | None = None,
) -> None:
    await RiskRepository(db_session).create(
        {
            "zone_id": UUID(zone_id),
            "score": score,
            "level": level,
            "confidence": 100,
            "is_emergency_override": False,
            "categories": [],
            "contributors": contributors or [],
            "explanation": "seeded",
            "engine_version": "CRE-v1.0.0",
            "trigger_source": "scheduler_tick",
            "evaluation_duration_ms": 1,
            "evaluated_at": evaluated_at,
        }
    )


async def _create_recommendation(
    db_session: AsyncSession,
    *,
    zone_id: str,
    template_id: str,
    first_generated_at: datetime,
    acknowledged_at: datetime | None = None,
) -> None:
    await RecommendationRepository(db_session).create(
        {
            "zone_id": UUID(zone_id),
            "identity_key": f"{zone_id}:{template_id}",
            "template_id": template_id,
            "category": "gas_hazard",
            "priority": "high",
            "title": "Evacuate and ventilate",
            "action_text": "Ventilate the zone and evacuate non-essential personnel.",
            "expected_outcomes": ["Gas concentration drops below alarm threshold"],
            "rationale": "H2S elevated",
            "source_rule_ids": ["RULE_H2S_ELEVATED"],
            "target_entity": {"entity_type": "zone", "entity_id": zone_id, "label": "Zone"},
            "engine_version": "REC-v1.0.0",
            "first_generated_at": first_generated_at,
            "last_seen_at": first_generated_at,
            "acknowledged_at": acknowledged_at,
        }
    )


# --- empty-state shape ---


async def test_safety_trend_empty_state(client: AsyncClient) -> None:
    _, zone_id = await _create_plant_and_zone(client)

    response = await client.get("/api/v1/reports/safety-trend", params={"zone_id": zone_id})
    assert response.status_code == 200
    body = response.json()

    # Default window is trailing 30 days -> falls in the (14, 120] day bucket -> weekly.
    assert body["period_granularity"] == "week"
    assert len(body["periods"]) > 0
    assert body["total_incidents_opened"] == 0
    assert body["total_incidents_resolved"] == 0
    assert body["trend_direction"] == "flat"
    assert body["trend_summary"] == "No incidents were opened during this period."
    for point in body["periods"]:
        assert point["incidents_opened"] == 0
        assert point["incidents_resolved"] == 0
        assert point["normal_count"] == 0


async def test_zone_hazard_analysis_empty_state(client: AsyncClient) -> None:
    await _create_plant_and_zone(client)

    response = await client.get("/api/v1/reports/zones-hazards")
    assert response.status_code == 200
    body = response.json()

    assert len(body["zones"]) == 1
    zone = body["zones"][0]
    assert zone["incident_count"] == 0
    assert zone["open_incident_count"] == 0
    assert zone["reportable_incident_count"] == 0
    assert zone["avg_risk_score"] is None
    assert zone["top_category"] is None
    assert body["hazard_categories"] == []
    assert body["top_rules"] == []


async def test_incident_response_empty_state(client: AsyncClient) -> None:
    _, zone_id = await _create_plant_and_zone(client)

    response = await client.get("/api/v1/reports/incident-response", params={"zone_id": zone_id})
    assert response.status_code == 200
    body = response.json()

    assert body["incidents_resolved_count"] == 0
    assert body["incidents_closed_count"] == 0
    assert body["mean_time_to_resolve_hours"] is None
    assert body["mean_time_to_close_hours"] is None
    assert body["recommendations_acknowledged_count"] == 0
    assert body["mean_time_to_acknowledge_minutes"] is None
    assert len(body["classification_breakdown"]) == 4
    assert all(c["count"] == 0 for c in body["classification_breakdown"])
    assert body["top_recommendation_templates"] == []


# --- aggregation math ---


async def test_safety_trend_buckets_and_direction(client: AsyncClient, db_session: AsyncSession) -> None:
    _, zone_id = await _create_plant_and_zone(client)

    since = datetime(2026, 1, 1, tzinfo=timezone.utc)
    until = datetime(2026, 1, 4, tzinfo=timezone.utc)

    # day0: two opened; day1: one of those two resolved; day2: one more opened.
    # All rows use status="resolved" (irrelevant to this report) to avoid tripping the
    # "one open incident per zone" partial unique index across these three rows.
    await _create_incident(
        db_session,
        zone_id=zone_id,
        opened_at=datetime(2026, 1, 1, 10, tzinfo=timezone.utc),
        resolved_at=datetime(2026, 1, 2, 9, tzinfo=timezone.utc),
        status="resolved",
    )
    await _create_incident(
        db_session,
        zone_id=zone_id,
        opened_at=datetime(2026, 1, 1, 14, tzinfo=timezone.utc),
        status="resolved",
    )
    await _create_incident(
        db_session,
        zone_id=zone_id,
        opened_at=datetime(2026, 1, 3, 8, tzinfo=timezone.utc),
        status="resolved",
    )

    await _create_snapshot(
        db_session, zone_id=zone_id, evaluated_at=datetime(2026, 1, 1, 12, tzinfo=timezone.utc), level="high"
    )
    await _create_snapshot(
        db_session, zone_id=zone_id, evaluated_at=datetime(2026, 1, 3, 9, tzinfo=timezone.utc), level="critical"
    )

    response = await client.get(
        "/api/v1/reports/safety-trend",
        params={"since": since.isoformat(), "until": until.isoformat(), "zone_id": zone_id},
    )
    assert response.status_code == 200
    body = response.json()

    assert body["period_granularity"] == "day"
    assert len(body["periods"]) == 3
    day0, day1, day2 = body["periods"]

    assert day0["incidents_opened"] == 2
    assert day0["incidents_resolved"] == 0
    assert day0["high_count"] == 1

    assert day1["incidents_opened"] == 0
    assert day1["incidents_resolved"] == 1

    assert day2["incidents_opened"] == 1
    assert day2["incidents_resolved"] == 0
    assert day2["critical_count"] == 1

    assert body["total_incidents_opened"] == 3
    assert body["total_incidents_resolved"] == 1
    # Midpoint splits Jan1 00:00-Jan4 00:00 at Jan2 12:00: first half has 2 opened, second has 1.
    assert body["trend_direction"] == "down"
    assert body["trend_summary"] == "Incidents opened fell from 2 to 1 across this period."


async def test_zone_hazard_analysis_aggregates_across_zones(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    _, zone_one = await _create_plant_and_zone(client, zone_code="ZN-01")
    zone_two_resp = (
        await client.post(
            "/api/v1/zones",
            json={
                "plant_id": (await client.get(f"/api/v1/zones/{zone_one}")).json()["plant_id"],
                "code": "ZN-02",
                "name": "Tank Farm",
                "zone_type": "tank_farm",
            },
        )
    ).json()
    zone_two = zone_two_resp["id"]

    since = datetime(2026, 1, 1, tzinfo=timezone.utc)
    until = datetime(2026, 1, 8, tzinfo=timezone.utc)
    t0 = datetime(2026, 1, 2, tzinfo=timezone.utc)

    await _create_incident(
        db_session, zone_id=zone_one, opened_at=t0, status="open", classification="reportable_incident"
    )
    await _create_incident(
        db_session, zone_id=zone_one, opened_at=t0, status="resolved", classification="operational_episode"
    )
    await _create_snapshot(
        db_session,
        zone_id=zone_one,
        evaluated_at=t0,
        score=50,
        contributors=[
            {"rule_id": "RULE_H2S_ELEVATED", "category": "gas_hazard"},
            {"rule_id": "RULE_H2S_ELEVATED", "category": "gas_hazard"},
        ],
    )

    response = await client.get(
        "/api/v1/reports/zones-hazards", params={"since": since.isoformat(), "until": until.isoformat()}
    )
    assert response.status_code == 200
    body = response.json()

    assert len(body["zones"]) == 2
    # Sorted incident_count desc: zone_one (2) before zone_two (0).
    assert body["zones"][0]["zone_id"] == zone_one
    assert body["zones"][0]["incident_count"] == 2
    assert body["zones"][0]["open_incident_count"] == 1
    assert body["zones"][0]["reportable_incident_count"] == 1
    assert body["zones"][0]["avg_risk_score"] == 50.0
    assert body["zones"][0]["top_category"] == "gas_hazard"

    assert body["zones"][1]["zone_id"] == zone_two
    assert body["zones"][1]["incident_count"] == 0
    assert body["zones"][1]["avg_risk_score"] is None
    assert body["zones"][1]["top_category"] is None

    assert body["hazard_categories"] == [{"category": "gas_hazard", "trigger_count": 2}]

    assert len(body["top_rules"]) == 1
    top_rule = body["top_rules"][0]
    assert top_rule["rule_id"] == "RULE_H2S_ELEVATED"
    assert top_rule["category"] == "gas_hazard"
    assert top_rule["trigger_count"] == 2
    expected_rule = next(r for r in ALL_RULES if r.rule_id == "RULE_H2S_ELEVATED")
    assert top_rule["description"] == expected_rule.description


async def test_incident_response_aggregates_timings_and_counts(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    _, zone_id = await _create_plant_and_zone(client)

    t0 = datetime(2026, 2, 1, 8, tzinfo=timezone.utc)
    since = datetime(2026, 2, 1, tzinfo=timezone.utc)
    until = datetime(2026, 2, 2, tzinfo=timezone.utc)

    await _create_incident(
        db_session,
        zone_id=zone_id,
        opened_at=t0,
        resolved_at=t0.replace(hour=10),  # +2h
        closed_at=t0.replace(hour=13),  # +5h
        classification="safety_incident",
    )
    await _create_recommendation(
        db_session,
        zone_id=zone_id,
        template_id="TEMPLATE_EVACUATE",
        first_generated_at=t0,
        acknowledged_at=datetime(2026, 2, 1, 8, 30, tzinfo=timezone.utc),
    )

    response = await client.get(
        "/api/v1/reports/incident-response",
        params={"since": since.isoformat(), "until": until.isoformat(), "zone_id": zone_id},
    )
    assert response.status_code == 200
    body = response.json()

    assert body["incidents_resolved_count"] == 1
    assert body["incidents_closed_count"] == 1
    assert body["mean_time_to_resolve_hours"] == 2.0
    assert body["mean_time_to_close_hours"] == 5.0
    assert body["recommendations_acknowledged_count"] == 1
    assert body["mean_time_to_acknowledge_minutes"] == 30.0

    breakdown = {c["classification"]: c["count"] for c in body["classification_breakdown"]}
    assert breakdown["safety_incident"] == 1
    assert breakdown["operational_episode"] == 0
    assert breakdown["near_miss"] == 0
    assert breakdown["reportable_incident"] == 0

    assert len(body["top_recommendation_templates"]) == 1
    template = body["top_recommendation_templates"][0]
    assert template["template_id"] == "TEMPLATE_EVACUATE"
    assert template["trigger_count"] == 1
    assert template["category"] == "gas_hazard"
