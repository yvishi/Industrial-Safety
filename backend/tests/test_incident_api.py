from uuid import UUID

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.correlation_engine.decide import ThresholdState
from app.repositories.event import EventRepository
from app.repositories.incident import IncidentRepository
from app.repositories.recommendation import RecommendationRepository
from app.repositories.risk import RiskRepository
from app.repositories.zone import ZoneRepository
from app.risk_engine.config.defaults import DEFAULT_RISK_CONFIG
from app.risk_engine.facts_builder import ZoneFactsBuilder
from app.services.incident import IncidentService
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


async def _reconcile(
    client: AsyncClient,
    db_session: AsyncSession,
    zone_id: str,
    threshold_states: dict[UUID, ThresholdState],
) -> None:
    """Drives one full scheduler-tick pass (risk -> recommendation -> incident), mirroring
    RiskScheduler.run_once() — the scheduler itself doesn't run in tests (ASGITransport skips
    the app lifespan). `threshold_states` must be the same dict passed across every call within
    a test — it's what RiskScheduler itself owns across ticks (see IncidentService.reconcile's
    docstring); a fresh dict per call would reset the debounce counters every time."""
    builder = ZoneFactsBuilder(db_session)
    risk_service = RiskService(RiskRepository(db_session), builder, EventRepository(db_session), DEFAULT_RISK_CONFIG)
    recommendation_service = RecommendationService(
        RecommendationRepository(db_session),
        ZoneRepository(db_session),
        EventRepository(db_session),
        RiskRepository(db_session),
    )
    incident_service = IncidentService(
        IncidentRepository(db_session),
        RecommendationRepository(db_session),
        EventRepository(db_session),
        ZoneRepository(db_session),
    )
    facts = await builder.build_for_zone(UUID(zone_id), DEFAULT_RISK_CONFIG)
    assessment, _ = await risk_service.evaluate(facts)
    active_recommendations = await recommendation_service.reconcile(assessment)
    await incident_service.reconcile(assessment, facts, active_recommendations, threshold_states)


async def test_no_incident_for_freshly_seeded_zone(client: AsyncClient, db_session: AsyncSession) -> None:
    _, zone_id = await _create_plant_and_zone(client)
    await _reconcile(client, db_session, zone_id, {})

    response = await client.get("/api/v1/incidents", params={"zone_id": zone_id})
    assert response.status_code == 200
    assert response.json()["items"] == []


async def test_emergency_shutdown_opens_an_incident_immediately(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """ESD bypasses the open debounce entirely (see correlation_engine/decide.py) — one tick
    is enough."""
    _, zone_id = await _create_plant_and_zone(client)
    await client.patch(f"/api/v1/zones/{zone_id}", json={"emergency_shutdown_active": True})
    await _reconcile(client, db_session, zone_id, {})

    response = await client.get("/api/v1/incidents", params={"zone_id": zone_id})
    body = response.json()
    assert body["total"] == 1
    incident = body["items"][0]
    assert incident["status"] == "open"
    assert incident["origin"] == "system_detected"
    assert incident["risk_severity_at_open"] == "critical"
    assert incident["title"]
    assert incident["summary"]

    events = (await client.get("/api/v1/events", params={"zone_id": zone_id})).json()
    event_types = {e["event_type"] for e in events["items"]}
    assert "incident_opened" in event_types


async def test_incident_identity_is_stable_across_reconcile_passes(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    _, zone_id = await _create_plant_and_zone(client)
    state: dict = {}
    await client.patch(f"/api/v1/zones/{zone_id}", json={"emergency_shutdown_active": True})
    await _reconcile(client, db_session, zone_id, state)
    first_id = (await client.get("/api/v1/incidents", params={"zone_id": zone_id})).json()["items"][0]["id"]

    await _reconcile(client, db_session, zone_id, state)
    items = (await client.get("/api/v1/incidents", params={"zone_id": zone_id})).json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == first_id


async def test_incident_auto_resolves_after_debounce_when_condition_clears(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    _, zone_id = await _create_plant_and_zone(client)
    state: dict = {}
    await client.patch(f"/api/v1/zones/{zone_id}", json={"emergency_shutdown_active": True})
    await _reconcile(client, db_session, zone_id, state)
    incident_id = (await client.get("/api/v1/incidents", params={"zone_id": zone_id})).json()["items"][0]["id"]

    await client.patch(f"/api/v1/zones/{zone_id}", json={"emergency_shutdown_active": False})
    # min_ticks_to_resolve defaults to 2 consecutive non-qualifying ticks.
    await _reconcile(client, db_session, zone_id, state)
    await _reconcile(client, db_session, zone_id, state)

    incident = (await client.get(f"/api/v1/incidents/{incident_id}")).json()
    assert incident["status"] == "resolved"
    assert incident["resolved_at"] is not None

    events = (await client.get("/api/v1/events", params={"zone_id": zone_id})).json()
    event_types = {e["event_type"] for e in events["items"]}
    assert "incident_resolved" in event_types


async def test_manual_incident_create_note_escalate_close_lifecycle(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    _, zone_id = await _create_plant_and_zone(client)

    create_resp = await client.post(
        "/api/v1/incidents",
        json={
            "primary_zone_id": zone_id,
            "title": "Worker slipped near Tank 4",
            "description": "Wet floor near the access ladder; no gas/risk trigger involved.",
            "classification": "safety_incident",
        },
    )
    assert create_resp.status_code == 201
    incident = create_resp.json()
    assert incident["origin"] == "manual"
    assert incident["risk_severity_at_open"] is None
    assert incident["status"] == "open"

    note_resp = await client.post(
        f"/api/v1/incidents/{incident['id']}/notes", json={"note_text": "First aid administered on site."}
    )
    assert note_resp.status_code == 200

    escalate_resp = await client.post(
        f"/api/v1/incidents/{incident['id']}/escalate", json={"classification": "reportable_incident"}
    )
    assert escalate_resp.status_code == 200
    assert escalate_resp.json()["classification"] == "reportable_incident"

    # A reportable_incident cannot close without root_cause + incident_severity.
    bad_close = await client.post(f"/api/v1/incidents/{incident['id']}/close", json={})
    assert bad_close.status_code == 409

    close_resp = await client.post(
        f"/api/v1/incidents/{incident['id']}/close",
        json={
            "root_cause": "Wet floor warning sign was missing.",
            "incident_severity": "minor",
            "corrective_actions": ["Install permanent wet-floor signage"],
        },
    )
    assert close_resp.status_code == 200
    closed = close_resp.json()
    assert closed["status"] == "closed"
    assert closed["closed_at"] is not None
    assert closed["resolved_at"] is not None  # manual incidents skip an explicit resolve step
    assert closed["incident_severity"] == "minor"

    events = (await client.get("/api/v1/events", params={"zone_id": zone_id})).json()
    event_types = {e["event_type"] for e in events["items"]}
    assert {"incident_opened", "incident_note_added", "incident_escalated", "incident_closed"} <= event_types


async def test_cannot_close_an_already_closed_incident(client: AsyncClient, db_session: AsyncSession) -> None:
    _, zone_id = await _create_plant_and_zone(client)
    incident = (
        await client.post(
            "/api/v1/incidents", json={"primary_zone_id": zone_id, "title": "First", "description": "d"}
        )
    ).json()
    await client.post(f"/api/v1/incidents/{incident['id']}/close", json={})

    second_close = await client.post(f"/api/v1/incidents/{incident['id']}/close", json={})
    assert second_close.status_code == 409


async def test_manual_incident_blocks_a_second_open_incident_for_same_zone(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    _, zone_id = await _create_plant_and_zone(client)
    await client.post("/api/v1/incidents", json={"primary_zone_id": zone_id, "title": "First", "description": "d"})

    second = await client.post(
        "/api/v1/incidents", json={"primary_zone_id": zone_id, "title": "Second", "description": "d"}
    )
    assert second.status_code == 409


async def test_manual_incident_is_not_touched_by_the_correlation_engine(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """A manual incident occupies the zone's one-open-incident slot; reconcile() must not crash
    on its null peak_risk_severity, nor auto-resolve or auto-open a second incident over it."""
    _, zone_id = await _create_plant_and_zone(client)
    await client.post("/api/v1/incidents", json={"primary_zone_id": zone_id, "title": "Manual", "description": "d"})

    await client.patch(f"/api/v1/zones/{zone_id}", json={"emergency_shutdown_active": True})
    await _reconcile(client, db_session, zone_id, {})  # must not raise

    items = (await client.get("/api/v1/incidents", params={"zone_id": zone_id})).json()["items"]
    assert len(items) == 1
    assert items[0]["origin"] == "manual"
    assert items[0]["status"] == "open"


async def test_get_unknown_incident_returns_404(client: AsyncClient) -> None:
    response = await client.get("/api/v1/incidents/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
