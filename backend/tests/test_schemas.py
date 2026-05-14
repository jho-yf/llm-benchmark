import pytest
from pydantic import ValidationError

from app.schemas.schedule import ScheduleCreate, ScheduleUpdate


def test_schedule_create_valid():
    data = {
        "name": "test",
        "cron_expr": "0 2 * * 0",
        "llm": {
            "provider": "openai",
            "api_base": "https://api.openai.com/v1",
            "api_key": "sk-test",
            "auth_type": "bearer",
            "model_id": "gpt-4o",
        },
        "benchmark": {
            "name": "MMLU",
            "category": "knowledge",
            "config": {"tasks": ["mmlu"]},
        },
    }
    s = ScheduleCreate(**data)
    assert s.name == "test"
    assert s.llm.provider == "openai"
    assert s.benchmark.config == {"tasks": ["mmlu"]}


def test_schedule_create_missing_required():
    with pytest.raises(ValidationError):
        ScheduleCreate(name="test", cron_expr="* * * * *")


def test_schedule_update_partial():
    u = ScheduleUpdate(name="new-name")
    assert u.name == "new-name"
    assert u.cron_expr is None
    assert u.llm is None


def test_schedule_create_default_auth():
    data = {
        "name": "t",
        "cron_expr": "* * *",
        "llm": {
            "provider": "ollama",
            "api_base": "http://localhost:11434/v1",
            "model_id": "llama3",
        },
        "benchmark": {
            "name": "test",
            "category": "knowledge",
            "config": {},
        },
    }
    s = ScheduleCreate(**data)
    assert s.llm.auth_type == "bearer"
    assert s.llm.api_key is None
