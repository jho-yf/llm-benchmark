from datetime import datetime

from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    provider: str = Field(default="custom", max_length=50)
    api_base: str = Field(..., max_length=500)
    api_key: str | None = None
    auth_type: str = Field(default="bearer", max_length=20)
    model_id: str = Field(..., max_length=200)
    stream: bool = Field(default=True)
    params: dict | None = None


class BenchmarkConfig(BaseModel):
    name: str = Field(..., max_length=200)
    category: str = Field(..., max_length=50)
    config: dict
    metrics: dict | None = None
    params: dict | None = None


class ScheduleCreate(BaseModel):
    name: str = Field(..., max_length=200)
    cron_expr: str = Field(..., max_length=100)
    llm: LLMConfig
    benchmark: BenchmarkConfig


class ScheduleUpdate(BaseModel):
    name: str | None = Field(None, max_length=200)
    cron_expr: str | None = Field(None, max_length=100)
    enabled: bool | None = None
    llm: LLMConfig | None = None
    benchmark: BenchmarkConfig | None = None


class ScheduleResponse(BaseModel):
    id: int
    name: str
    cron_expr: str
    enabled: bool
    last_run_at: datetime | None
    next_run_at: datetime | None
    created_at: datetime
    llm_provider: str
    llm_api_base: str
    llm_api_key: str | None
    llm_auth_type: str
    llm_model_id: str
    llm_stream: bool = True
    llm_params: dict | None
    benchmark_name: str
    benchmark_category: str
    benchmark_config: dict
    benchmark_metrics: dict | None
    benchmark_params: dict | None

    model_config = {"from_attributes": True}


class ScheduleTestConnection(BaseModel):
    provider: str = Field(default="custom", max_length=50)
    api_base: str = Field(..., max_length=500)
    api_key: str | None = None
    auth_type: str = Field(default="bearer", max_length=20)
    model_id: str = Field(..., max_length=200)
    params: dict | None = None
    schedule_id: int | None = None
