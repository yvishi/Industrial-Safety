from uuid import UUID

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.event import EventRepository
from app.repositories.recommendation import RecommendationRepository
from app.repositories.risk import RiskRepository
from app.repositories.zone import ZoneRepository
from app.risk_engine.config.defaults import DEFAULT_RISK_CONFIG
from app.risk_engine.facts_builder import ZoneFactsBuilder
from app.services.recommendation import RecommendationService
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


async def _reconcile(client: AsyncClient, db_session: AsyncSession, zone_id: str) -> None:
    """Drives one reconciliation pass directly, mirroring how RiskScheduler.run_once() calls
    it — the scheduler itself doesn't run in tests (ASGITransport skips the app lifespan)."""
    builder = ZoneFactsBuilder(db_session)
    risk_service = RiskService(RiskRepository(db_session), builder, DEFAULT_RISK_CONFIG)
    recommendation_service = RecommendationService(
        RecommendationRepository(db_session), ZoneRepository(db_session), EventRepository(db_session)
    )
    facts = await builder.build_for_zone(UUID(zone_id), DEFAULT_RISK_CONFIG)
    assessment, _ = await risk_service.evaluate(facts)
    await recommendation_service.reconcile(assessment)


async def test_no_recommendations_for_freshly_seeded_zone(client: AsyncClient, db_session: AsyncSession) -> None:
    _, zone_id = await _create_plant_and_zone(client)
    await _reconcile(client, db_session, zone_id)

    response = await client.get(f"/api/v1/recommendations/zones/{zone_id}")
    assert response.status_code == 200
    assert response.json() == []


async def test_emergency_shutdown_generates_a_recommendation(client: AsyncClient, db_session: AsyncSession) -> None:
    _, zone_id = await _create_plant_and_zone(client)
    await client.patch(f"/api/v1/zones/{zone_id}", json={"emergency_shutdown_active": True})
    await _reconcile(client, db_session, zone_id)

    response = await client.get(f"/api/v1/recommendations/zones/{zone_id}")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    rec = body[0]
    assert rec["template_id"] == "confirm_esd_response"
    assert rec["priority"] == "critical"
    assert rec["state"] == "new"
    assert rec["zone_id"] == zone_id
    assert rec["target_entity"]["entity_type"] == "zone"
    assert rec["source_rule_ids"] == ["RULE_EMERGENCY_SHUTDOWN_ACTIVE"]


async def test_recommendation_auto_resolves_when_condition_clears(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    _, zone_id = await _create_plant_and_zone(client)
    await client.patch(f"/api/v1/zones/{zone_id}", json={"emergency_shutdown_active": True})
    await _reconcile(client, db_session, zone_id)
    assert len((await client.get(f"/api/v1/recommendations/zones/{zone_id}")).json()) == 1

    await client.patch(f"/api/v1/zones/{zone_id}", json={"emergency_shutdown_active": False})
    await _reconcile(client, db_session, zone_id)

    active = (await client.get(f"/api/v1/recommendations/zones/{zone_id}")).json()
    assert active == []

    history = (await client.get(f"/api/v1/recommendations/zones/{zone_id}/history")).json()
    assert history["total"] == 1
    assert history["items"][0]["state"] == "resolved"


async def test_recommendation_identity_is_stable_across_reconcile_passes(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    _, zone_id = await _create_plant_and_zone(client)
    await client.patch(f"/api/v1/zones/{zone_id}", json={"emergency_shutdown_active": True})
    await _reconcile(client, db_session, zone_id)
    first_id = (await client.get(f"/api/v1/recommendations/zones/{zone_id}")).json()[0]["id"]

    await _reconcile(client, db_session, zone_id)
    second = (await client.get(f"/api/v1/recommendations/zones/{zone_id}")).json()
    assert len(second) == 1
    assert second[0]["id"] == first_id


async def test_recommendation_recurs_after_resolving(client: AsyncClient, db_session: AsyncSession) -> None:
    """A condition that clears and later comes back must produce a new lifecycle row, not
    collide with the identity_key of the row it already resolved — regression test for a bug
    caught by live-running the scheduler against a real simulator (see identity_key's partial
    unique index, scoped to non-resolved rows only)."""
    _, zone_id = await _create_plant_and_zone(client)

    await client.patch(f"/api/v1/zones/{zone_id}", json={"emergency_shutdown_active": True})
    await _reconcile(client, db_session, zone_id)
    first = (await client.get(f"/api/v1/recommendations/zones/{zone_id}")).json()
    assert len(first) == 1
    first_id = first[0]["id"]

    await client.patch(f"/api/v1/zones/{zone_id}", json={"emergency_shutdown_active": False})
    await _reconcile(client, db_session, zone_id)
    assert (await client.get(f"/api/v1/recommendations/zones/{zone_id}")).json() == []

    await client.patch(f"/api/v1/zones/{zone_id}", json={"emergency_shutdown_active": True})
    await _reconcile(client, db_session, zone_id)
    second = (await client.get(f"/api/v1/recommendations/zones/{zone_id}")).json()
    assert len(second) == 1
    assert second[0]["id"] != first_id
    assert second[0]["template_id"] == "confirm_esd_response"

    history = (await client.get(f"/api/v1/recommendations/zones/{zone_id}/history")).json()
    assert history["total"] == 2


async def test_acknowledge_transitions_state_and_logs_event(client: AsyncClient, db_session: AsyncSession) -> None:
    _, zone_id = await _create_plant_and_zone(client)
    await client.patch(f"/api/v1/zones/{zone_id}", json={"emergency_shutdown_active": True})
    await _reconcile(client, db_session, zone_id)
    recommendation_id = (await client.get(f"/api/v1/recommendations/zones/{zone_id}")).json()[0]["id"]

    response = await client.post(f"/api/v1/recommendations/{recommendation_id}/acknowledge")
    assert response.status_code == 200
    assert response.json()["state"] == "acknowledged"

    events = (await client.get("/api/v1/events", params={"zone_id": zone_id})).json()
    event_types = {e["event_type"] for e in events["items"]}
    assert "recommendation_acknowledged" in event_types

    # Acknowledged recommendations stay active (v1 has no dismiss) until the condition clears.
    active = (await client.get(f"/api/v1/recommendations/zones/{zone_id}")).json()
    assert len(active) == 1
    assert active[0]["state"] == "acknowledged"


async def test_resolve_transitions_state_and_logs_event(client: AsyncClient, db_session: AsyncSession) -> None:
    _, zone_id = await _create_plant_and_zone(client)
    await client.patch(f"/api/v1/zones/{zone_id}", json={"emergency_shutdown_active": True})
    await _reconcile(client, db_session, zone_id)
    recommendation_id = (await client.get(f"/api/v1/recommendations/zones/{zone_id}")).json()[0]["id"]

    response = await client.post(f"/api/v1/recommendations/{recommendation_id}/resolve")
    assert response.status_code == 200
    assert response.json()["state"] == "resolved"

    events = (await client.get("/api/v1/events", params={"zone_id": zone_id})).json()
    event_types = {e["event_type"] for e in events["items"]}
    assert "recommendation_resolved" in event_types

    active = (await client.get(f"/api/v1/recommendations/zones/{zone_id}")).json()
    assert active == []


async def test_acknowledge_unknown_recommendation_returns_404(client: AsyncClient) -> None:
    response = await client.post("/api/v1/recommendations/00000000-0000-0000-0000-000000000000/acknowledge")
    assert response.status_code == 404


async def test_plant_recommendation_summary_shape(client: AsyncClient, db_session: AsyncSession) -> None:
    plant = (await client.post("/api/v1/plants", json={"code": "TST-01", "name": "Test Plant"})).json()
    zone_one = (
        await client.post(
            "/api/v1/zones",
            json={"plant_id": plant["id"], "code": "ZN-01", "name": "Zone One", "zone_type": "crude_distillation"},
        )
    ).json()
    zone_two = (
        await client.post(
            "/api/v1/zones",
            json={"plant_id": plant["id"], "code": "ZN-02", "name": "Zone Two", "zone_type": "tank_farm"},
        )
    ).json()
    await client.patch(f"/api/v1/zones/{zone_two['id']}", json={"emergency_shutdown_active": True})
    await _reconcile(client, db_session, zone_one["id"])
    await _reconcile(client, db_session, zone_two["id"])

    response = await client.get("/api/v1/recommendations/plant")
    assert response.status_code == 200
    body = response.json()

    assert len(body["top_recommendations"]) == 1
    assert body["top_recommendations"][0]["zone_id"] == zone_two["id"]
    assert body["top_recommendations"][0]["zone_name"] == "Zone Two"
    assert body["counts_by_priority"] == {"critical": 1}
    assert body["plant_wide_emergency_active"] is True


async def test_recommendation_template_catalog_endpoint(client: AsyncClient) -> None:
    response = await client.get("/api/v1/recommendations/templates")
    assert response.status_code == 200
    entries = response.json()
    assert len(entries) == 17
    all_source_rules = {rule_id for entry in entries for rule_id in entry["source_rule_ids"]}
    assert len(all_source_rules) == 21
