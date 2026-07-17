from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.event import EventRepository
from app.repositories.risk import RiskRepository
from app.risk_engine.config.defaults import DEFAULT_RISK_CONFIG
from app.risk_engine.facts_builder import ZoneFactsBuilder
from app.services.risk import RiskService


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


async def test_zone_risk_returns_normal_for_freshly_seeded_zone(client: AsyncClient) -> None:
    _, zone_id = await _create_plant_and_zone(client)

    response = await client.get(f"/api/v1/risk/zones/{zone_id}")
    assert response.status_code == 200
    body = response.json()

    assert body["score"] == 0
    assert body["level"] == "normal"
    assert body["contributors"] == []
    assert body["triggered_rules"] == []
    assert body["is_emergency_override"] is False
    assert body["confidence_score"] == 100
    assert body["confidence_label"] == "high"
    assert len(body["categories"]) == 7
    assert body["previous_score"] is None
    assert body["engine_version"] == "CRE-v1.0.0"


async def test_zone_risk_returns_404_for_unknown_zone(client: AsyncClient) -> None:
    response = await client.get("/api/v1/risk/zones/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


async def test_emergency_shutdown_flag_forces_critical_immediately(client: AsyncClient) -> None:
    _, zone_id = await _create_plant_and_zone(client)

    patch_response = await client.patch(f"/api/v1/zones/{zone_id}", json={"emergency_shutdown_active": True})
    assert patch_response.status_code == 200
    assert patch_response.json()["emergency_shutdown_active"] is True

    risk_response = await client.get(f"/api/v1/risk/zones/{zone_id}")
    assert risk_response.status_code == 200
    body = risk_response.json()
    assert body["level"] == "critical"
    assert body["is_emergency_override"] is True
    assert "RULE_EMERGENCY_SHUTDOWN_ACTIVE" in body["triggered_rules"]

    events_response = await client.get("/api/v1/events", params={"zone_id": zone_id})
    assert events_response.status_code == 200
    event_types = {e["event_type"] for e in events_response.json()["items"]}
    assert "emergency_shutdown_activated" in event_types


async def test_emergency_shutdown_clear_logs_cleared_event(client: AsyncClient) -> None:
    _, zone_id = await _create_plant_and_zone(client)
    await client.patch(f"/api/v1/zones/{zone_id}", json={"emergency_shutdown_active": True})

    clear_response = await client.patch(f"/api/v1/zones/{zone_id}", json={"emergency_shutdown_active": False})
    assert clear_response.status_code == 200

    events_response = await client.get("/api/v1/events", params={"zone_id": zone_id})
    event_types = {e["event_type"] for e in events_response.json()["items"]}
    assert "emergency_shutdown_cleared" in event_types

    risk_response = await client.get(f"/api/v1/risk/zones/{zone_id}")
    assert risk_response.json()["level"] == "normal"


async def test_plant_risk_summary_shape(client: AsyncClient) -> None:
    plant = (await client.post("/api/v1/plants", json={"code": "TST-01", "name": "Test Plant"})).json()
    await client.post(
        "/api/v1/zones",
        json={"plant_id": plant["id"], "code": "ZN-01", "name": "Zone One", "zone_type": "crude_distillation"},
    )
    zone_two = (
        await client.post(
            "/api/v1/zones",
            json={"plant_id": plant["id"], "code": "ZN-02", "name": "Zone Two", "zone_type": "tank_farm"},
        )
    ).json()
    await client.patch(f"/api/v1/zones/{zone_two['id']}", json={"emergency_shutdown_active": True})

    response = await client.get("/api/v1/risk/plant")
    assert response.status_code == 200
    body = response.json()

    assert len(body["zones"]) == 2
    assert body["plant_wide_emergency_active"] is True
    assert body["highest_risk_zone_id"] == zone_two["id"]


async def test_rule_catalog_endpoint(client: AsyncClient) -> None:
    response = await client.get("/api/v1/risk/rules")
    assert response.status_code == 200
    entries = response.json()
    assert len(entries) == 21
    rule_ids = {e["rule_id"] for e in entries}
    assert "RULE_EMERGENCY_SHUTDOWN_ACTIVE" in rule_ids
    assert all("category" in e and "description" in e and "weight" in e for e in entries)


async def test_persist_if_changed_writes_only_on_meaningful_change(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    _, zone_id_str = await _create_plant_and_zone(client)
    from uuid import UUID

    zone_id = UUID(zone_id_str)

    builder = ZoneFactsBuilder(db_session)
    repository = RiskRepository(db_session)
    service = RiskService(repository, builder, EventRepository(db_session), DEFAULT_RISK_CONFIG)

    facts = await builder.build_for_zone(zone_id, DEFAULT_RISK_CONFIG)

    first = await service.evaluate_and_persist_if_changed(facts)
    assert first is not None

    second = await service.evaluate_and_persist_if_changed(facts)
    assert second is None

    items, total = await repository.history_for_zone(zone_id)
    assert total == 1

    await client.patch(f"/api/v1/zones/{zone_id}", json={"emergency_shutdown_active": True})
    changed_facts = await builder.build_for_zone(zone_id, DEFAULT_RISK_CONFIG)
    third = await service.evaluate_and_persist_if_changed(changed_facts)
    assert third is not None
    assert third.level == "critical"

    items, total = await repository.history_for_zone(zone_id)
    assert total == 2

    changes_response = await client.get("/api/v1/risk/changes")
    assert changes_response.status_code == 200
    changes = changes_response.json()
    assert len(changes) == 2
    assert changes[0]["level"] == "critical"
    assert changes[0]["score_delta"] is not None
