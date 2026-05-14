import pytest

SCHEDULE_PAYLOAD = {
    "name": "test-job",
    "cron_expr": "0 2 * * 0",
    "llm": {
        "provider": "openai",
        "api_base": "https://api.openai.com/v1",
        "api_key": "sk-test",
        "auth_type": "bearer",
        "model_id": "gpt-4o",
    },
    "benchmark": {
        "name": "MMLU 5-shot",
        "category": "knowledge",
        "config": {"tasks": ["mmlu"], "num_fewshot": {"mmlu": 5}},
    },
}


@pytest.mark.asyncio
async def test_create_schedule(client):
    resp = await client.post("/api/schedules", json=SCHEDULE_PAYLOAD)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "test-job"
    assert data["llm_model_id"] == "gpt-4o"
    assert data["benchmark_name"] == "MMLU 5-shot"


@pytest.mark.asyncio
async def test_list_schedules(client):
    await client.post("/api/schedules", json=SCHEDULE_PAYLOAD)
    resp = await client.get("/api/schedules")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_update_schedule(client):
    r = await client.post("/api/schedules", json=SCHEDULE_PAYLOAD)
    job_id = r.json()["id"]
    resp = await client.put(f"/api/schedules/{job_id}", json={"name": "updated"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "updated"


@pytest.mark.asyncio
async def test_toggle_schedule(client):
    r = await client.post("/api/schedules", json=SCHEDULE_PAYLOAD)
    job_id = r.json()["id"]
    resp = await client.post(f"/api/schedules/{job_id}/toggle")
    assert resp.status_code == 200
    assert resp.json()["enabled"] is False


@pytest.mark.asyncio
async def test_delete_schedule(client):
    r = await client.post("/api/schedules", json=SCHEDULE_PAYLOAD)
    job_id = r.json()["id"]
    resp = await client.delete(f"/api/schedules/{job_id}")
    assert resp.status_code == 204
    resp = await client.get("/api/schedules")
    assert len(resp.json()) == 0


@pytest.mark.asyncio
async def test_delete_not_found(client):
    resp = await client.delete("/api/schedules/999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_test_connection(client):
    resp = await client.post("/api/schedules/test-connection", json={
        "provider": "openai",
        "api_base": "https://api.openai.com/v1",
        "api_key": "sk-fake",
        "auth_type": "api_key",
        "model_id": "gpt-4o",
    })
    assert resp.status_code == 200
    assert "success" in resp.json()
