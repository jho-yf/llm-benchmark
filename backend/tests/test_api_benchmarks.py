import pytest


@pytest.mark.asyncio
async def test_list_presets(client):
    resp = await client.get("/api/benchmarks/presets")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 8
    assert data[0]["id"]  # has id field
    assert data[0]["config"]["tasks"]


@pytest.mark.asyncio
async def test_list_categories(client):
    resp = await client.get("/api/benchmarks/categories")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    assert "id" in data[0]
    assert "name" in data[0]
