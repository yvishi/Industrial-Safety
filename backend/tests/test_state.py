from httpx import AsyncClient


async def test_state_returns_404_without_a_plant(client: AsyncClient) -> None:
    response = await client.get("/api/v1/state")
    assert response.status_code == 404


async def test_state_snapshot_shape(client: AsyncClient) -> None:
    plant = (await client.post("/api/v1/plants", json={"code": "TST-01", "name": "Test Plant"})).json()
    zone = (
        await client.post(
            "/api/v1/zones",
            json={
                "plant_id": plant["id"],
                "code": "ZN-01",
                "name": "Test Zone",
                "zone_type": "processing_unit",
            },
        )
    ).json()

    response = await client.get("/api/v1/state")
    assert response.status_code == 200
    state = response.json()

    assert state["plant"]["id"] == plant["id"]
    assert len(state["zones"]) == 1
    zone_state = state["zones"][0]
    assert zone_state["zone"]["id"] == zone["id"]
    assert zone_state["workers"] == []
    assert zone_state["equipment"] == []
    assert zone_state["sensors"] == []
    assert zone_state["active_permit_count"] == 0
    assert state["active_permits"] == []
    assert state["recent_events"] == []
