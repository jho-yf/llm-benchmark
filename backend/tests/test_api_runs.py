import pytest


@pytest.mark.asyncio
async def test_list_runs_empty(client):
    resp = await client.get("/api/runs")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_get_run_not_found(client):
    resp = await client.get("/api/runs/999")
    assert resp.status_code == 404
