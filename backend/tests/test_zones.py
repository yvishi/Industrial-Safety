from httpx import AsyncClient


async def _create_plant(client: AsyncClient, code: str = "TST-01") -> str:
    response = await client.post("/api/v1/plants", json={"code": code, "name": "Test Plant"})
    assert response.status_code == 201
    return response.json()["id"]


async def test_zone_crud_roundtrip(client: AsyncClient) -> None:
    plant_id = await _create_plant(client)

    create_response = await client.post(
        "/api/v1/zones",
        json={
            "plant_id": plant_id,
            "code": "ZN-01",
            "name": "Test Zone",
            "zone_type": "control_room",
        },
    )
    assert create_response.status_code == 201
    zone = create_response.json()
    assert zone["code"] == "ZN-01"

    get_response = await client.get(f"/api/v1/zones/{zone['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Test Zone"

    list_response = await client.get("/api/v1/zones", params={"plant_id": plant_id})
    assert list_response.status_code == 200
    body = list_response.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == zone["id"]


async def test_zone_duplicate_code_is_rejected(client: AsyncClient) -> None:
    plant_id = await _create_plant(client)
    payload = {
        "plant_id": plant_id,
        "code": "ZN-02",
        "name": "First Zone",
        "zone_type": "tank_farm",
    }

    first = await client.post("/api/v1/zones", json=payload)
    assert first.status_code == 201

    second = await client.post("/api/v1/zones", json={**payload, "name": "Second Zone"})
    assert second.status_code == 409


async def test_get_missing_zone_returns_404(client: AsyncClient) -> None:
    response = await client.get("/api/v1/zones/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
